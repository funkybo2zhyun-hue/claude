import AppKit

/// 테스트패턴 창: 픽셀 입력 → 미리보기 → PNG 저장 / 외부 디스플레이에 바로 표출
@MainActor
final class TestPatternController: NSObject, NSWindowDelegate, NSTextFieldDelegate {
    private var window: NSWindow?
    private let widthField = NSTextField()
    private let heightField = NSTextField()
    private let cabWField = NSTextField()
    private let cabHField = NSTextField()
    private let presetPopup = NSPopUpButton()
    private let displayPopup = NSPopUpButton()
    private let placePopup = NSPopUpButton()
    private let preview = NSImageView()
    private let infoLabel = NSTextField(labelWithString: "")
    private var outputs: [String: NSWindow] = [:]   // 디스플레이 UUID → 표출 창
    private let defaults = UserDefaults.standard

    private static let presets: [(String, Int, Int)] = [
        ("2560 × 768 (10:3)", 2560, 768),
        ("2048 × 1024 (2:1)", 2048, 1024),
        ("1920 × 1080 (16:9)", 1920, 1080),
        ("3840 × 2160 (4K)", 3840, 2160),
        ("3840 × 1080 (32:9)", 3840, 1080),
        ("1536 × 768 (2:1)", 1536, 768),
        ("1024 × 1024 (1:1)", 1024, 1024),
    ]

    enum Placement: Int { case topLeft = 0, center = 1, stretch = 2 }

    var isShowingOnDisplay: Bool { !outputs.isEmpty }

    // MARK: 창

    func show() {
        if window == nil { build() }
        reloadDisplays()
        updatePreview()
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKeyAndOrderFront(nil)
    }

    private func build() {
        let win = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 760, height: 560),
                           styleMask: [.titled, .closable, .miniaturizable, .resizable],
                           backing: .buffered, defer: false)
        win.title = "MBOX 테스트패턴"
        win.isReleasedWhenClosed = false
        win.delegate = self
        win.minSize = NSSize(width: 620, height: 460)

        for f in [widthField, heightField, cabWField, cabHField] {
            f.delegate = self
            f.alignment = .right
            f.widthAnchor.constraint(equalToConstant: 72).isActive = true
        }
        widthField.stringValue = defaults.string(forKey: "tpWidth") ?? "2560"
        heightField.stringValue = defaults.string(forKey: "tpHeight") ?? "768"
        cabWField.stringValue = defaults.string(forKey: "tpCabW") ?? ""
        cabHField.stringValue = defaults.string(forKey: "tpCabH") ?? ""
        cabWField.placeholderString = "없음"
        cabHField.placeholderString = "없음"

        presetPopup.addItem(withTitle: "자주 쓰는 크기…")
        for p in Self.presets { presetPopup.addItem(withTitle: p.0) }
        presetPopup.target = self
        presetPopup.action = #selector(presetChosen)

        let sizeRow = row([label("가로"), widthField, label("×  세로"), heightField, label("px"), spacer(12), presetPopup])
        let fromDisplay = button("선택한 디스플레이 해상도로", #selector(useDisplaySize))
        let cabRow = row([label("LED 캐비닛(선택)"), cabWField, label("×"), cabHField, label("px"), spacer(12), fromDisplay])

        preview.imageScaling = .scaleProportionallyUpOrDown
        preview.wantsLayer = true
        preview.layer?.backgroundColor = NSColor.black.cgColor
        preview.setContentHuggingPriority(.defaultLow, for: .vertical)
        preview.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        infoLabel.textColor = .secondaryLabelColor

        let save = button("PNG로 저장…", #selector(savePNG))
        save.keyEquivalent = "s"
        save.keyEquivalentModifierMask = .command
        let saveRow = row([save, infoLabel])

        placePopup.addItems(withTitles: ["왼쪽 위 기준 1:1 픽셀", "가운데 1:1 픽셀", "화면에 꽉 채우기"])
        placePopup.selectItem(at: defaults.integer(forKey: "tpPlacement"))
        let showBtn = button("▶︎ 바로 표출", #selector(showOnDisplay))
        let hideBtn = button("■ 표출 끄기", #selector(hideAll))
        let showRow = row([label("표출할 디스플레이"), displayPopup, placePopup, showBtn, hideBtn])

        let stack = NSStackView(views: [sizeRow, cabRow, preview, saveRow, divider(), showRow])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 12
        stack.edgeInsets = NSEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)
        stack.translatesAutoresizingMaskIntoConstraints = false
        let content = NSView()
        content.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor),
            stack.topAnchor.constraint(equalTo: content.topAnchor),
            stack.bottomAnchor.constraint(equalTo: content.bottomAnchor),
            preview.leadingAnchor.constraint(equalTo: stack.leadingAnchor, constant: 16),
            preview.trailingAnchor.constraint(equalTo: stack.trailingAnchor, constant: -16),
            preview.heightAnchor.constraint(greaterThanOrEqualToConstant: 200),
        ])
        win.contentView = content
        win.center()
        window = win
    }

    private func label(_ s: String) -> NSTextField { NSTextField(labelWithString: s) }

    private func spacer(_ w: CGFloat) -> NSView {
        let v = NSView()
        v.widthAnchor.constraint(equalToConstant: w).isActive = true
        return v
    }

    private func divider() -> NSView {
        let b = NSBox()
        b.boxType = .separator
        return b
    }

    private func button(_ title: String, _ action: Selector) -> NSButton {
        NSButton(title: title, target: self, action: action)
    }

    private func row(_ views: [NSView]) -> NSStackView {
        let s = NSStackView(views: views)
        s.orientation = .horizontal
        s.spacing = 8
        s.alignment = .centerY
        return s
    }

    // MARK: 입력

    private func currentSpec() -> TestPatternSpec? {
        let w = Int(widthField.stringValue.trimmingCharacters(in: .whitespaces)) ?? 0
        let h = Int(heightField.stringValue.trimmingCharacters(in: .whitespaces)) ?? 0
        guard (32...TestPattern.maxSide).contains(w), (32...TestPattern.maxSide).contains(h) else { return nil }
        let cw = Int(cabWField.stringValue.trimmingCharacters(in: .whitespaces)) ?? 0
        let ch = Int(cabHField.stringValue.trimmingCharacters(in: .whitespaces)) ?? 0
        let cabOK = cw >= 16 && ch >= 16
        return TestPatternSpec(width: w, height: h, cabinetW: cabOK ? cw : 0, cabinetH: cabOK ? ch : 0)
    }

    func controlTextDidChange(_ obj: Notification) {
        defaults.set(widthField.stringValue, forKey: "tpWidth")
        defaults.set(heightField.stringValue, forKey: "tpHeight")
        defaults.set(cabWField.stringValue, forKey: "tpCabW")
        defaults.set(cabHField.stringValue, forKey: "tpCabH")
        updatePreview()
    }

    @objc private func presetChosen() {
        let i = presetPopup.indexOfSelectedItem - 1
        presetPopup.selectItem(at: 0)
        guard i >= 0 && i < Self.presets.count else { return }
        widthField.stringValue = String(Self.presets[i].1)
        heightField.stringValue = String(Self.presets[i].2)
        controlTextDidChange(Notification(name: NSControl.textDidChangeNotification))
    }

    @objc private func useDisplaySize() {
        guard let screen = selectedScreen(), let mode = CGDisplayCopyDisplayMode(screen.displayID) else { return }
        widthField.stringValue = String(mode.pixelWidth)
        heightField.stringValue = String(mode.pixelHeight)
        controlTextDidChange(Notification(name: NSControl.textDidChangeNotification))
    }

    private func updatePreview() {
        guard let spec = currentSpec() else {
            preview.image = nil
            infoLabel.stringValue = "가로·세로를 32 ~ \(TestPattern.maxSide) 사이 숫자로 넣어 주세요"
            return
        }
        if let img = TestPattern.render(spec) {
            preview.image = NSImage(cgImage: img, size: NSSize(width: spec.width, height: spec.height))
        }
        infoLabel.stringValue = "\(spec.width) × \(spec.height) px · \(TestPattern.aspectText(spec.width, spec.height))"
    }

    // MARK: 저장

    @objc private func savePNG() {
        guard let spec = currentSpec(), let img = TestPattern.render(spec), let win = window else { return }
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.png]
        panel.nameFieldStringValue = "MBOX_TestPattern_\(spec.width)x\(spec.height).png"
        panel.directoryURL = FileManager.default.urls(for: .desktopDirectory, in: .userDomainMask).first
        panel.beginSheetModal(for: win) { [weak self] resp in
            guard resp == .OK, let url = panel.url else { return }
            do {
                try writePNG(img, to: url)
                self?.infoLabel.stringValue = "저장됨: \(url.lastPathComponent)"
            } catch {
                self?.infoLabel.stringValue = "저장 실패: \(error.localizedDescription)"
            }
        }
    }

    // MARK: 표출

    func reloadDisplays() {
        let prev = displayPopup.selectedItem?.representedObject as? String
        displayPopup.removeAllItems()
        let screens = NSScreen.screens
        for (i, s) in screens.enumerated() {
            let px = CGDisplayCopyDisplayMode(s.displayID).map { " \($0.pixelWidth)×\($0.pixelHeight)" } ?? ""
            displayPopup.addItem(withTitle: "\(s.localizedName)\(px)\(i == 0 ? " (메인)" : "")")
            displayPopup.lastItem?.representedObject = s.uuidString
        }
        if let prev, let idx = displayPopup.itemArray.firstIndex(where: { ($0.representedObject as? String) == prev }) {
            displayPopup.selectItem(at: idx)
        } else if screens.count > 1 {
            displayPopup.selectItem(at: 1)   // 기본: 첫 번째 외부 디스플레이
        }
    }

    private func selectedScreen() -> NSScreen? {
        guard let id = displayPopup.selectedItem?.representedObject as? String else { return nil }
        return NSScreen.screens.first { $0.uuidString == id }
    }

    @objc private func showOnDisplay() {
        guard let spec = currentSpec(), let img = TestPattern.render(spec) else { return }
        guard let screen = selectedScreen() else {
            infoLabel.stringValue = "표출할 디스플레이를 골라 주세요"
            return
        }
        let place = Placement(rawValue: placePopup.indexOfSelectedItem) ?? .topLeft
        defaults.set(place.rawValue, forKey: "tpPlacement")
        show(image: img, on: screen, placement: place)
        infoLabel.stringValue = "표출 중: \(screen.localizedName) (화면 클릭하면 꺼짐)"
    }

    func show(image: CGImage, on screen: NSScreen, placement: Placement) {
        let key = screen.uuidString
        let win = outputs[key] ?? {
            let w = NSWindow(contentRect: screen.frame, styleMask: .borderless, backing: .buffered, defer: false, screen: screen)
            w.level = .screenSaver
            w.backgroundColor = .black
            w.isOpaque = true
            w.hasShadow = false
            w.isReleasedWhenClosed = false
            w.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary, .ignoresCycle]
            return w
        }()
        let view = PatternView(image: image, placement: placement) { [weak self] in self?.hide(key: key) }
        win.contentView = view
        win.setFrame(screen.frame, display: true)
        win.orderFrontRegardless()
        outputs[key] = win
    }

    @objc func hideAll() {
        for key in Array(outputs.keys) { hide(key: key) }
        infoLabel.stringValue = "표출 껐음"
    }

    private func hide(key: String) {
        outputs[key]?.orderOut(nil)
        outputs[key] = nil
    }
}

/// 표출 창 안에서 이미지를 실제 픽셀 1:1(또는 꽉 채우기)로 그린다
final class PatternView: NSView {
    private let image: CGImage
    private let placement: TestPatternController.Placement
    private let onClick: () -> Void

    init(image: CGImage, placement: TestPatternController.Placement, onClick: @escaping () -> Void) {
        self.image = image
        self.placement = placement
        self.onClick = onClick
        super.init(frame: .zero)
    }

    required init?(coder: NSCoder) { fatalError() }

    override func draw(_ dirtyRect: NSRect) {
        NSColor.black.setFill()
        bounds.fill()
        guard let ctx = NSGraphicsContext.current?.cgContext else { return }
        ctx.interpolationQuality = placement == .stretch ? .high : .none
        let scale = window?.backingScaleFactor ?? 1
        let w = CGFloat(image.width) / scale
        let h = CGFloat(image.height) / scale
        let rect: CGRect
        switch placement {
        case .topLeft: rect = CGRect(x: 0, y: bounds.height - h, width: w, height: h)
        case .center: rect = CGRect(x: ((bounds.width - w) / 2).rounded(), y: ((bounds.height - h) / 2).rounded(), width: w, height: h)
        case .stretch: rect = bounds
        }
        ctx.draw(image, in: rect)
    }

    override func mouseDown(with event: NSEvent) { onClick() }
}

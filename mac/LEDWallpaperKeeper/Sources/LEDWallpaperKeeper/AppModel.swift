import AppKit
import ScreenCaptureKit
import ServiceManagement
import SwiftUI

struct DisplayInfo: Identifiable, Hashable {
    let id: String      // 다시 연결해도 같은 UUID
    let name: String
    let pixelW: Int
    let pixelH: Int
    let isMain: Bool
    var sizeText: String { "\(pixelW)×\(pixelH)" }
}

enum Placement: Int, CaseIterable, Identifiable {
    case topLeft = 0, center = 1, stretch = 2
    var id: Int { rawValue }
    var label: String {
        switch self {
        case .topLeft: return "왼쪽 위 1:1"
        case .center: return "가운데 1:1"
        case .stretch: return "꽉 채움"
        }
    }
}

/// 앱 전체 상태. 메뉴바 메뉴와 메인 창이 같은 모델을 쓴다.
@MainActor
final class AppModel: ObservableObject {
    static let presets: [(String, Int, Int)] = [
        ("2560 × 768  (10:3)", 2560, 768),
        ("2048 × 1024  (2:1)", 2048, 1024),
        ("1920 × 1080  (16:9)", 1920, 1080),
        ("3840 × 2160  (4K)", 3840, 2160),
        ("3840 × 1080  (32:9)", 3840, 1080),
        ("1536 × 768  (2:1)", 1536, 768),
        ("1024 × 1024  (1:1)", 1024, 1024),
    ]

    private let defaults = UserDefaults.standard
    private let mock: Bool
    private var flip: [String: Bool] = [:]
    private var outputs: [String: NSWindow] = [:]

    // 바탕화면 백업
    @Published var displays: [DisplayInfo] = []
    @Published var disabled: Set<String> {
        didSet { defaults.set(Array(disabled), forKey: "disabledDisplays") }
    }
    @Published var captureStatus = "아직 캡처 안 함"
    @Published var isCapturing = false
    @Published var hasScreenPermission: Bool

    // 테스트패턴
    @Published var style: TestPatternStyle {
        didSet { defaults.set(style.rawValue, forKey: "tpStyle"); renderPreview() }
    }
    @Published var widthText: String { didSet { defaults.set(widthText, forKey: "tpWidth"); renderPreview() } }
    @Published var heightText: String { didSet { defaults.set(heightText, forKey: "tpHeight"); renderPreview() } }
    @Published var cabWText: String { didSet { defaults.set(cabWText, forKey: "tpCabW"); renderPreview() } }
    @Published var cabHText: String { didSet { defaults.set(cabHText, forKey: "tpCabH"); renderPreview() } }
    @Published var targetID: String = ""
    @Published var placement: Placement {
        didSet { defaults.set(placement.rawValue, forKey: "tpPlacement") }
    }
    @Published var preview: NSImage?
    @Published var patternMessage = ""
    @Published var showingOn: Set<String> = []
    @Published var launchAtLogin: Bool {
        didSet {
            guard !mock, launchAtLogin != (SMAppService.mainApp.status == .enabled) else { return }
            do {
                if launchAtLogin { try SMAppService.mainApp.register() } else { try SMAppService.mainApp.unregister() }
            } catch {
                captureStatus = "자동 실행 설정 실패: \(error.localizedDescription)"
            }
        }
    }

    init(mock: Bool = false) {
        self.mock = mock
        disabled = Set(UserDefaults.standard.stringArray(forKey: "disabledDisplays") ?? [])
        hasScreenPermission = mock ? true : CGPreflightScreenCaptureAccess()
        let d = UserDefaults.standard
        let savedStyle = TestPatternStyle(rawValue: d.integer(forKey: "tpStyle")) ?? .neon
        style = TestPatternStyle.selectable.contains(savedStyle) ? savedStyle : .neon
        widthText = d.string(forKey: "tpWidth") ?? "2560"
        heightText = d.string(forKey: "tpHeight") ?? "768"
        cabWText = d.string(forKey: "tpCabW") ?? "128"
        cabHText = d.string(forKey: "tpCabH") ?? "128"
        placement = Placement(rawValue: d.integer(forKey: "tpPlacement")) ?? .topLeft
        launchAtLogin = mock ? false : SMAppService.mainApp.status == .enabled
        if mock {
            displays = [
                DisplayInfo(id: "main", name: "Built-in Retina Display", pixelW: 3024, pixelH: 1964, isMain: true),
                DisplayInfo(id: "led1", name: "NovaStar LED", pixelW: 2560, pixelH: 768, isMain: false),
                DisplayInfo(id: "led2", name: "PVP 출력 (DELL)", pixelW: 1920, pixelH: 1080, isMain: false),
            ]
            disabled = ["led2"]
            targetID = "led1"
            captureStatus = "마지막 캡처 18:02:11 · 1개 적용"
            showingOn = ["led1"]
        } else {
            refreshDisplays()
        }
        renderPreview()
    }

    // MARK: 디스플레이

    var externalDisplays: [DisplayInfo] { displays.filter { !$0.isMain } }

    func refreshDisplays() {
        guard !mock else { return }
        hasScreenPermission = CGPreflightScreenCaptureAccess()
        displays = NSScreen.screens.enumerated().map { i, s in
            let mode = CGDisplayCopyDisplayMode(s.displayID)
            return DisplayInfo(id: s.uuidString, name: s.localizedName,
                               pixelW: mode?.pixelWidth ?? Int(s.frame.width * s.backingScaleFactor),
                               pixelH: mode?.pixelHeight ?? Int(s.frame.height * s.backingScaleFactor),
                               isMain: i == 0)
        }
        if !displays.contains(where: { $0.id == targetID }) {
            targetID = externalDisplays.first?.id ?? displays.first?.id ?? ""
        }
        showingOn = showingOn.filter { id in displays.contains { $0.id == id } }
    }

    func screen(for id: String) -> NSScreen? { NSScreen.screens.first { $0.uuidString == id } }

    func isEnabled(_ d: DisplayInfo) -> Bool { !disabled.contains(d.id) }

    func setEnabled(_ d: DisplayInfo, _ on: Bool) {
        if on { disabled.remove(d.id) } else { disabled.insert(d.id) }
    }

    func requestPermission() {
        CGRequestScreenCaptureAccess()
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture") {
            NSWorkspace.shared.open(url)
        }
    }

    // MARK: 캡처 → 바탕화면

    var saveDir: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        let dir = base.appendingPathComponent("LEDWallpaperKeeper", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    func openFolder() { NSWorkspace.shared.open(saveDir) }

    func captureAll() async {
        guard !mock, !isCapturing else { return }
        refreshDisplays()
        let screens = externalDisplays.filter(isEnabled).compactMap { screen(for: $0.id) }
        guard !screens.isEmpty else {
            captureStatus = "켜진 외부 디스플레이가 없어요 (메인 모니터는 건드리지 않음)"
            return
        }
        isCapturing = true
        defer { isCapturing = false }
        do {
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
            var done = 0
            var failed: [String] = []
            for screen in screens {
                guard let display = content.displays.first(where: { $0.displayID == screen.displayID }) else {
                    failed.append(screen.localizedName)
                    continue
                }
                do {
                    let image = try await capture(display: display, screen: screen)
                    let url = try saveCapture(image, for: screen)
                    try NSWorkspace.shared.setDesktopImageURL(url, for: screen, options: [
                        .imageScaling: NSNumber(value: NSImageScaling.scaleAxesIndependently.rawValue),
                        .allowClipping: NSNumber(value: true),
                        .fillColor: NSColor.black,
                    ])
                    done += 1
                } catch {
                    failed.append(screen.localizedName)
                }
            }
            let time = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
            captureStatus = "마지막 캡처 \(time) · \(done)개 적용"
            if !failed.isEmpty { captureStatus += " · 실패: " + failed.joined(separator: ", ") }
        } catch {
            hasScreenPermission = CGPreflightScreenCaptureAccess()
            captureStatus = "캡처 실패: 화면 기록 권한을 확인해 주세요"
        }
    }

    private func capture(display: SCDisplay, screen: NSScreen) async throws -> CGImage {
        let filter = SCContentFilter(display: display, excludingWindows: [])
        let config = SCStreamConfiguration()
        if let mode = CGDisplayCopyDisplayMode(screen.displayID) {
            config.width = mode.pixelWidth
            config.height = mode.pixelHeight
        } else {
            config.width = Int(CGFloat(display.width) * screen.backingScaleFactor)
            config.height = Int(CGFloat(display.height) * screen.backingScaleFactor)
        }
        config.showsCursor = false
        return try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: config)
    }

    private func saveCapture(_ image: CGImage, for screen: NSScreen) throws -> URL {
        // 같은 파일명을 다시 쓰면 macOS가 바탕화면을 안 바꾸므로 A/B 번갈아 저장
        let key = screen.uuidString
        let next = !(flip[key] ?? false)
        flip[key] = next
        let safeName = screen.localizedName.replacingOccurrences(of: "/", with: "_")
        let url = saveDir.appendingPathComponent("\(safeName)_\(key.prefix(8))_\(next ? "A" : "B").png")
        try writePNG(image, to: url)
        return url
    }

    // MARK: 테스트패턴

    var currentSpec: TestPatternSpec? {
        let w = Int(widthText.trimmingCharacters(in: .whitespaces)) ?? 0
        let h = Int(heightText.trimmingCharacters(in: .whitespaces)) ?? 0
        guard (32...TestPattern.maxSide).contains(w), (32...TestPattern.maxSide).contains(h) else { return nil }
        return spec(width: w, height: h, style: style)
    }

    func spec(width: Int, height: Int, style: TestPatternStyle) -> TestPatternSpec {
        let cw = Int(cabWText.trimmingCharacters(in: .whitespaces)) ?? 0
        let ch = Int(cabHText.trimmingCharacters(in: .whitespaces)) ?? 0
        let ok = cw >= 16 && ch >= 16
        return TestPatternSpec(width: width, height: height, cabinetW: ok ? cw : 0, cabinetH: ok ? ch : 0, style: style)
    }

    var sizeSummary: String {
        guard let s = currentSpec else { return "가로·세로를 32 ~ \(TestPattern.maxSide) 사이로 넣어 주세요" }
        var t = "\(s.width) × \(s.height) px · \(TestPattern.aspectText(s.width, s.height))"
        if s.cabinetW > 0 {
            t += " · 캐비닛 \((s.width + s.cabinetW - 1) / s.cabinetW)×\((s.height + s.cabinetH - 1) / s.cabinetH)"
        }
        return t
    }

    func applyPreset(_ w: Int, _ h: Int) {
        widthText = String(w)
        heightText = String(h)
    }

    func useTargetDisplaySize() {
        guard let d = displays.first(where: { $0.id == targetID }) else { return }
        applyPreset(d.pixelW, d.pixelH)
    }

    func renderPreview() {
        guard let s = currentSpec else { preview = nil; return }
        // 미리보기는 비율 그대로 작게 (최대 1280px), 저장·표출은 원래 크기
        let k = min(1, 1280 / Double(max(s.width, s.height)))
        var small = s
        if k < 1 {
            small.width = max(32, Int(Double(s.width) * k))
            small.height = max(32, Int(Double(s.height) * k))
            if s.cabinetW > 0 {
                small.cabinetW = max(1, Int(Double(s.cabinetW) * k))
                small.cabinetH = max(1, Int(Double(s.cabinetH) * k))
            }
        }
        guard let img = TestPattern.render(small) else { preview = nil; return }
        preview = NSImage(cgImage: img, size: NSSize(width: img.width, height: img.height))
    }

    func savePNG() {
        guard let s = currentSpec, let img = TestPattern.render(s) else { return }
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.png]
        panel.nameFieldStringValue = "MBOX_TestPattern_\(s.style == .swiss ? "White" : "Neon")_\(s.width)x\(s.height).png"
        panel.directoryURL = FileManager.default.urls(for: .desktopDirectory, in: .userDomainMask).first
        NSApp.activate(ignoringOtherApps: true)
        guard panel.runModal() == .OK, let url = panel.url else { return }
        do {
            try writePNG(img, to: url)
            patternMessage = "저장됨: \(url.lastPathComponent)"
        } catch {
            patternMessage = "저장 실패: \(error.localizedDescription)"
        }
    }

    /// 창에서 고른 설정(크기·시안·위치) 그대로 표출
    func showPattern() {
        guard let s = currentSpec else { return }
        show(spec: s, on: targetID, placement: placement)
    }

    /// 메뉴바에서 바로: 그 디스플레이 해상도에 꼭 맞게 표출
    func showNative(style: TestPatternStyle, on id: String) {
        guard let d = displays.first(where: { $0.id == id }) else { return }
        show(spec: spec(width: d.pixelW, height: d.pixelH, style: style), on: id, placement: .topLeft)
    }

    private func show(spec: TestPatternSpec, on id: String, placement: Placement) {
        guard !mock, let screen = screen(for: id), let img = TestPattern.render(spec) else {
            patternMessage = "표출할 디스플레이를 찾지 못했어요"
            return
        }
        let win = outputs[id] ?? {
            let w = NSWindow(contentRect: screen.frame, styleMask: .borderless, backing: .buffered, defer: false, screen: screen)
            w.level = .screenSaver
            w.backgroundColor = .black
            w.isOpaque = true
            w.hasShadow = false
            w.isReleasedWhenClosed = false
            w.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary, .ignoresCycle]
            return w
        }()
        win.contentView = PatternView(image: img, placement: placement) { [weak self] in self?.hide(id) }
        win.setFrame(screen.frame, display: true)
        win.orderFrontRegardless()
        outputs[id] = win
        showingOn.insert(id)
        patternMessage = "표출 중: \(screen.localizedName) · 화면을 클릭하면 꺼져요"
    }

    func hide(_ id: String) {
        outputs[id]?.orderOut(nil)
        outputs[id] = nil
        showingOn.remove(id)
    }

    func hideAll() {
        for id in Array(outputs.keys) { hide(id) }
        showingOn.removeAll()
        patternMessage = "표출 껐어요"
    }

    func displayName(_ id: String) -> String { displays.first { $0.id == id }?.name ?? "" }
}

/// 표출 창 안에서 패턴을 실제 픽셀 1:1(또는 꽉 채움)로 그린다
final class PatternView: NSView {
    private let image: CGImage
    private let placement: Placement
    private let onClick: () -> Void

    init(image: CGImage, placement: Placement, onClick: @escaping () -> Void) {
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

extension NSScreen {
    var displayID: CGDirectDisplayID {
        (deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?.uint32Value ?? 0
    }

    /// 다시 연결해도 바뀌지 않는 디스플레이 고유값
    var uuidString: String {
        guard let uuid = CGDisplayCreateUUIDFromDisplayID(displayID)?.takeRetainedValue() else {
            return "id-\(displayID)"
        }
        return (CFUUIDCreateString(nil, uuid) as String?) ?? "id-\(displayID)"
    }
}

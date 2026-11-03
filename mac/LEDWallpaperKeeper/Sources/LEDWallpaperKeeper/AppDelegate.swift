import AppKit
import ScreenCaptureKit
import ServiceManagement
import UniformTypeIdentifiers

/// 외부 디스플레이(메인 모니터 제외) 각각에 지금 나가는 화면을 캡처해서
/// 그 디스플레이의 바탕화면으로 지정한다. 재생 프로그램이 튕기면 마지막 화면이 남는다.
@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private var statusItem: NSStatusItem!
    private var timer: Timer?
    private var isCapturing = false
    private var statusText = "아직 캡처 안 함"
    private var flip: [String: Bool] = [:]   // 디스플레이별 A/B 파일 번갈아 쓰기 (macOS 바탕화면 캐시 회피)
    private let defaults = UserDefaults.standard

    // MARK: 설정

    private static let intervals: [(String, TimeInterval)] = [
        ("3초", 3), ("5초", 5), ("10초", 10), ("30초", 30), ("1분", 60), ("5분", 300),
    ]
    /// 이 이름이 들어간 앱이 켜져 있을 때만 자동 캡처 (PVP3, ProPresenter)
    private static let playerKeywords = ["provideoplayer", "pvp", "propresenter", "renewedvision"]

    private var autoEnabled: Bool {
        get { defaults.object(forKey: "autoEnabled") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "autoEnabled") }
    }
    private var interval: TimeInterval {
        get { defaults.object(forKey: "interval") as? Double ?? 5 }
        set { defaults.set(newValue, forKey: "interval") }
    }
    private var onlyWhenPlayerRunning: Bool {
        get { defaults.object(forKey: "onlyWhenPlayerRunning") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "onlyWhenPlayerRunning") }
    }
    /// 끈 디스플레이 목록 (UUID). 새로 연결된 외부 디스플레이는 기본으로 켜짐.
    private var disabledDisplays: Set<String> {
        get { Set(defaults.stringArray(forKey: "disabledDisplays") ?? []) }
        set { defaults.set(Array(newValue), forKey: "disabledDisplays") }
    }

    private var saveDir: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        let dir = base.appendingPathComponent("LEDWallpaperKeeper", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    // MARK: 시작

    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.image = NSImage(systemSymbolName: "photo.on.rectangle.angled",
                                           accessibilityDescription: "LED 바탕화면 지킴이")
        let menu = NSMenu()
        menu.delegate = self
        statusItem.menu = menu

        if !CGPreflightScreenCaptureAccess() {
            CGRequestScreenCaptureAccess()
            statusText = "화면 기록 권한을 허용한 뒤 앱을 다시 켜 주세요"
        }
        restartTimer()
    }

    private func restartTimer() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(timeInterval: interval, target: self,
                                     selector: #selector(tick), userInfo: nil, repeats: true)
    }

    @objc private func tick() {
        guard autoEnabled else { return }
        if onlyWhenPlayerRunning && !isPlayerRunning() {
            statusText = "재생 프로그램 꺼짐 → 마지막 화면 유지 중"
            return
        }
        Task { await captureAll() }
    }

    private func isPlayerRunning() -> Bool {
        NSWorkspace.shared.runningApplications.contains { app in
            let name = (app.localizedName ?? "").lowercased()
            let bundle = (app.bundleIdentifier ?? "").lowercased()
            return Self.playerKeywords.contains { name.contains($0) || bundle.contains($0) }
        }
    }

    // MARK: 디스플레이

    /// 메인 모니터(메뉴 막대가 있는 첫 번째 화면)를 뺀 나머지 화면
    private func externalScreens() -> [NSScreen] {
        Array(NSScreen.screens.dropFirst())
    }

    private func targetScreens() -> [NSScreen] {
        let off = disabledDisplays
        return externalScreens().filter { !off.contains($0.uuidString) }
    }

    // MARK: 캡처 → 바탕화면

    private func captureAll() async {
        guard !isCapturing else { return }
        isCapturing = true
        defer { isCapturing = false }

        let screens = targetScreens()
        guard !screens.isEmpty else {
            statusText = "외부 디스플레이가 없음 (메인 모니터는 건드리지 않음)"
            return
        }
        do {
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
            var done: [String] = []
            var failed: [String] = []
            for screen in screens {
                guard let display = content.displays.first(where: { $0.displayID == screen.displayID }) else {
                    failed.append(screen.localizedName)
                    continue
                }
                do {
                    let image = try await capture(display: display, screen: screen)
                    let url = try save(image, for: screen)
                    try NSWorkspace.shared.setDesktopImageURL(url, for: screen, options: [
                        .imageScaling: NSNumber(value: NSImageScaling.scaleAxesIndependently.rawValue),
                        .allowClipping: NSNumber(value: true),
                        .fillColor: NSColor.black,
                    ])
                    done.append(screen.localizedName)
                } catch {
                    failed.append("\(screen.localizedName)(\(error.localizedDescription))")
                }
            }
            let time = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
            statusText = "마지막 캡처 \(time): \(done.count)개 적용"
            if !failed.isEmpty { statusText += " / 실패: " + failed.joined(separator: ", ") }
        } catch {
            statusText = "캡처 실패: 화면 기록 권한을 확인하세요 (\(error.localizedDescription))"
        }
    }

    private func capture(display: SCDisplay, screen: NSScreen) async throws -> CGImage {
        let filter = SCContentFilter(display: display, excludingWindows: [])
        let config = SCStreamConfiguration()
        // 실제 출력 픽셀 해상도로 캡처 (LED 컨트롤러 해상도 그대로)
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

    private func save(_ image: CGImage, for screen: NSScreen) throws -> URL {
        let key = screen.uuidString
        let next = !(flip[key] ?? false)
        flip[key] = next
        let safeName = screen.localizedName.replacingOccurrences(of: "/", with: "_")
        let url = saveDir.appendingPathComponent("\(safeName)_\(key.prefix(8))_\(next ? "A" : "B").png")
        guard let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw NSError(domain: "LEDWallpaperKeeper", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "파일을 만들 수 없음"])
        }
        CGImageDestinationAddImage(dest, image, nil)
        guard CGImageDestinationFinalize(dest) else {
            throw NSError(domain: "LEDWallpaperKeeper", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: "PNG 저장 실패"])
        }
        return url
    }

    // MARK: 메뉴

    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.removeAllItems()

        let status = NSMenuItem(title: statusText, action: nil, keyEquivalent: "")
        status.isEnabled = false
        menu.addItem(status)
        menu.addItem(.separator())

        menu.addItem(item("지금 캡처해서 바탕화면으로", #selector(captureNow), key: "c"))
        menu.addItem(.separator())

        let header = NSMenuItem(title: "적용할 외부 디스플레이 (메인 모니터 제외)", action: nil, keyEquivalent: "")
        header.isEnabled = false
        menu.addItem(header)
        let externals = externalScreens()
        if externals.isEmpty {
            let none = NSMenuItem(title: "   연결된 외부 디스플레이 없음", action: nil, keyEquivalent: "")
            none.isEnabled = false
            menu.addItem(none)
        }
        let off = disabledDisplays
        for screen in externals {
            let px = CGDisplayCopyDisplayMode(screen.displayID).map { " \($0.pixelWidth)x\($0.pixelHeight)" } ?? ""
            let it = item("   \(screen.localizedName)\(px)", #selector(toggleDisplay(_:)))
            it.representedObject = screen.uuidString
            it.state = off.contains(screen.uuidString) ? .off : .on
            menu.addItem(it)
        }
        menu.addItem(.separator())

        let auto = item("자동 캡처", #selector(toggleAuto))
        auto.state = autoEnabled ? .on : .off
        menu.addItem(auto)

        let intervalItem = NSMenuItem(title: "캡처 간격", action: nil, keyEquivalent: "")
        let sub = NSMenu()
        for (label, sec) in Self.intervals {
            let it = item(label, #selector(setInterval(_:)))
            it.representedObject = sec
            it.state = sec == interval ? .on : .off
            sub.addItem(it)
        }
        intervalItem.submenu = sub
        menu.addItem(intervalItem)

        let only = item("PVP3/ProPresenter 켜져 있을 때만 자동 캡처", #selector(toggleOnlyPlayer))
        only.state = onlyWhenPlayerRunning ? .on : .off
        menu.addItem(only)
        menu.addItem(.separator())

        let login = item("로그인할 때 자동 실행", #selector(toggleLogin))
        login.state = SMAppService.mainApp.status == .enabled ? .on : .off
        menu.addItem(login)
        menu.addItem(item("캡처 저장 폴더 열기", #selector(openFolder)))
        menu.addItem(.separator())
        menu.addItem(item("종료", #selector(quit), key: "q"))
    }

    private func item(_ title: String, _ action: Selector, key: String = "") -> NSMenuItem {
        let it = NSMenuItem(title: title, action: action, keyEquivalent: key)
        it.target = self
        return it
    }

    @objc private func captureNow() { Task { await captureAll() } }

    @objc private func toggleDisplay(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? String else { return }
        var off = disabledDisplays
        if off.contains(id) { off.remove(id) } else { off.insert(id) }
        disabledDisplays = off
    }

    @objc private func toggleAuto() { autoEnabled.toggle() }

    @objc private func setInterval(_ sender: NSMenuItem) {
        guard let sec = sender.representedObject as? TimeInterval else { return }
        interval = sec
        restartTimer()
    }

    @objc private func toggleOnlyPlayer() { onlyWhenPlayerRunning.toggle() }

    @objc private func toggleLogin() {
        do {
            if SMAppService.mainApp.status == .enabled {
                try SMAppService.mainApp.unregister()
            } else {
                try SMAppService.mainApp.register()
            }
        } catch {
            statusText = "자동 실행 설정 실패: \(error.localizedDescription)"
        }
    }

    @objc private func openFolder() { NSWorkspace.shared.open(saveDir) }

    @objc private func quit() { NSApp.terminate(nil) }
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

import AppKit
import SwiftUI

/// 상단 메뉴바에 늘 대기하는 앱.
/// 메인 창을 닫아도 꺼지지 않고, 메뉴바 메뉴에서 모든 기능을 바로 쓸 수 있다.
@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate, NSWindowDelegate {
    let model = AppModel()
    private var statusItem: NSStatusItem!
    private var window: NSWindow?

    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem.button {
            let img = NSImage(systemSymbolName: "display.2", accessibilityDescription: "MBOX LED Tools")
            img?.isTemplate = true
            button.image = img
            button.toolTip = "MBOX LED Tools"
        }
        let menu = NSMenu()
        menu.delegate = self
        statusItem.menu = menu

        NotificationCenter.default.addObserver(forName: NSApplication.didChangeScreenParametersNotification,
                                               object: nil, queue: .main) { [weak self] _ in
            MainActor.assumeIsolated { self?.model.refreshDisplays() }
        }
        if !CGPreflightScreenCaptureAccess() { CGRequestScreenCaptureAccess() }
        openWindow()
    }

    // 창이 닫혀도 앱은 계속 (메뉴바에 대기)
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        openWindow()
        return true
    }

    // MARK: 메인 창

    @objc func openWindow() {
        model.refreshDisplays()
        if window == nil {
            let host = NSHostingController(rootView: MainView(model: model))
            let win = NSWindow(contentViewController: host)
            win.title = "MBOX LED Tools"
            win.styleMask = [.titled, .closable, .miniaturizable]
            win.isReleasedWhenClosed = false
            win.delegate = self
            win.setFrameAutosaveName("MainWindow")
            win.center()
            window = win
        }
        // 창이 열려 있는 동안만 Dock에 보이기
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKeyAndOrderFront(nil)
    }

    func windowWillClose(_ notification: Notification) {
        // 창을 닫으면 Dock에서 숨기고 메뉴바에만 남김
        NSApp.setActivationPolicy(.accessory)
    }

    // MARK: 메뉴바 메뉴

    func menuNeedsUpdate(_ menu: NSMenu) {
        model.refreshDisplays()
        menu.removeAllItems()

        menu.addItem(disabled(model.captureStatus))
        menu.addItem(.separator())

        // 바탕화면 백업
        menu.addItem(header("바탕화면 백업"))
        menu.addItem(item("지금 캡처 → 외부 디스플레이 바탕화면", #selector(captureNow), symbol: "camera.viewfinder"))
        if model.externalDisplays.isEmpty {
            menu.addItem(disabled("   연결된 외부 디스플레이 없음"))
        }
        for d in model.externalDisplays {
            let it = item("\(d.name)  \(d.sizeText)", #selector(toggleDisplay(_:)))
            it.representedObject = d.id
            it.state = model.isEnabled(d) ? .on : .off
            it.indentationLevel = 1
            menu.addItem(it)
        }
        menu.addItem(.separator())

        // 테스트패턴
        menu.addItem(header("테스트패턴"))
        let showItem = NSMenuItem(title: "바로 표출 (디스플레이 해상도에 맞춤)", action: nil, keyEquivalent: "")
        showItem.image = NSImage(systemSymbolName: "play.rectangle", accessibilityDescription: nil)
        let showMenu = NSMenu()
        for d in model.displays {
            let sub = NSMenuItem(title: "\(d.name)\(d.isMain ? " (메인)" : "")  \(d.sizeText)", action: nil, keyEquivalent: "")
            let styles = NSMenu()
            for st in TestPatternStyle.selectable {
                let it = item(st.label, #selector(showNative(_:)))
                it.representedObject = ["id": d.id, "style": st.rawValue] as [String: Any]
                styles.addItem(it)
            }
            sub.submenu = styles
            if model.showingOn.contains(d.id) { sub.state = .on }
            showMenu.addItem(sub)
        }
        showItem.submenu = showMenu
        menu.addItem(showItem)
        if let s = model.currentSpec {
            menu.addItem(item("창 설정대로 표출 (\(s.width)×\(s.height) · \(s.style.label) → \(model.displayName(model.targetID)))",
                              #selector(showFromSettings), symbol: "slider.horizontal.3"))
            menu.addItem(item("PNG로 저장… (\(s.width)×\(s.height) · \(s.style.label))", #selector(savePNG), symbol: "square.and.arrow.down"))
        }
        if !model.showingOn.isEmpty {
            menu.addItem(item("표출 끄기", #selector(hidePatterns), symbol: "stop.fill"))
        }
        menu.addItem(.separator())

        menu.addItem(item("MBOX LED Tools 창 열기", #selector(openWindow), key: "o", symbol: "macwindow"))
        let login = item("로그인할 때 자동 실행", #selector(toggleLogin))
        login.state = model.launchAtLogin ? .on : .off
        menu.addItem(login)
        menu.addItem(item("캡처 폴더 열기", #selector(openFolder), symbol: "folder"))
        menu.addItem(.separator())
        menu.addItem(item("종료", #selector(quit), key: "q"))
    }

    private func item(_ title: String, _ action: Selector, key: String = "", symbol: String? = nil) -> NSMenuItem {
        let it = NSMenuItem(title: title, action: action, keyEquivalent: key)
        it.target = self
        if let symbol { it.image = NSImage(systemSymbolName: symbol, accessibilityDescription: nil) }
        return it
    }

    private func disabled(_ title: String) -> NSMenuItem {
        let it = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        it.isEnabled = false
        return it
    }

    private func header(_ title: String) -> NSMenuItem {
        if #available(macOS 14.0, *) { return NSMenuItem.sectionHeader(title: title) }
        return disabled(title)
    }

    @objc private func captureNow() { Task { await model.captureAll() } }

    @objc private func toggleDisplay(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? String,
              let d = model.displays.first(where: { $0.id == id }) else { return }
        model.setEnabled(d, !model.isEnabled(d))
    }

    @objc private func showNative(_ sender: NSMenuItem) {
        guard let info = sender.representedObject as? [String: Any],
              let id = info["id"] as? String,
              let raw = info["style"] as? Int,
              let st = TestPatternStyle(rawValue: raw) else { return }
        model.showNative(style: st, on: id)
    }

    @objc private func showFromSettings() { model.showPattern() }
    @objc private func savePNG() { model.savePNG() }
    @objc private func hidePatterns() { model.hideAll() }
    @objc private func toggleLogin() { model.launchAtLogin.toggle() }
    @objc private func openFolder() { model.openFolder() }
    @objc private func quit() { NSApp.terminate(nil) }
}

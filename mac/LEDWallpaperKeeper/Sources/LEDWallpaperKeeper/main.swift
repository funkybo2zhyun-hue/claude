import AppKit
import SwiftUI

let args = CommandLine.arguments

// 명령줄로 테스트패턴만 만들기 (빌드 확인·미리보기용)
// LEDWallpaperKeeper --render 가로 세로 출력.png [캐비닛가로 캐비닛세로 [시안번호 0/1/2]]
if args.count >= 5, args[1] == "--render", let w = Int(args[2]), let h = Int(args[3]) {
    var spec = TestPatternSpec(width: w, height: h)
    if args.count >= 7, let cw = Int(args[5]), let ch = Int(args[6]) {
        spec.cabinetW = cw
        spec.cabinetH = ch
    }
    if args.count >= 8, let st = Int(args[7]), let style = TestPatternStyle(rawValue: st) {
        spec.style = style
    }
    guard let img = TestPattern.render(spec) else {
        FileHandle.standardError.write("render failed\n".data(using: .utf8)!)
        exit(1)
    }
    do { try writePNG(img, to: URL(fileURLWithPath: args[4])) } catch {
        FileHandle.standardError.write("\(error)\n".data(using: .utf8)!)
        exit(1)
    }
    exit(0)
}

// 메인 창 화면을 PNG로 (빌드 서버에서 디자인 확인용, 가짜 디스플레이 목록 사용)
// LEDWallpaperKeeper --render-ui 출력.png [dark]
if args.count >= 3, args[1] == "--render-ui" {
    MainActor.assumeIsolated {
        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)
        let dark = args.count >= 4 && args[3] == "dark"
        let appearance = NSAppearance(named: dark ? .darkAqua : .aqua)
        NSAppearance.current = appearance
        let model = AppModel(mock: true)
        model.patternMessage = "표출 중: NovaStar LED · 화면을 클릭하면 꺼져요"
        let host = NSHostingView(rootView: MainView(model: model))
        host.appearance = appearance
        let size = host.fittingSize
        let win = NSWindow(contentRect: NSRect(origin: .zero, size: size), styleMask: [.titled],
                           backing: .buffered, defer: false)
        win.appearance = appearance
        win.contentView = host
        win.setFrameOrigin(NSPoint(x: 0, y: 0))
        win.orderFrontRegardless()
        host.layoutSubtreeIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(1.0))
        guard let rep = host.bitmapImageRepForCachingDisplay(in: host.bounds) else { exit(1) }
        host.cacheDisplay(in: host.bounds, to: rep)
        guard let data = rep.representation(using: .png, properties: [:]) else { exit(1) }
        try? data.write(to: URL(fileURLWithPath: args[2]))
        exit(0)
    }
}

MainActor.assumeIsolated {
    let app = NSApplication.shared
    let delegate = AppDelegate()
    app.delegate = delegate
    app.setActivationPolicy(.accessory)
    withExtendedLifetime(delegate) { app.run() }
}

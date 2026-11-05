import AppKit

// 명령줄로 테스트패턴만 만들기 (빌드 확인·미리보기용)
// LEDWallpaperKeeper --render 가로 세로 출력.png [캐비닛가로 캐비닛세로]
let args = CommandLine.arguments
if args.count >= 5, args[1] == "--render", let w = Int(args[2]), let h = Int(args[3]) {
    var spec = TestPatternSpec(width: w, height: h)
    if args.count >= 7, let cw = Int(args[5]), let ch = Int(args[6]) {
        spec.cabinetW = cw
        spec.cabinetH = ch
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

MainActor.assumeIsolated {
    let app = NSApplication.shared
    let delegate = AppDelegate()
    app.delegate = delegate
    app.setActivationPolicy(.accessory)
    withExtendedLifetime(delegate) { app.run() }
}

import AppKit
import CoreText
import UniformTypeIdentifiers

/// 테스트패턴 설정. 가로·세로는 픽셀 단위 그대로 나온다.
struct TestPatternSpec {
    var width: Int
    var height: Int
    /// LED 캐비닛(모듈) 크기. 0이면 자동 그리드.
    var cabinetW: Int = 0
    var cabinetH: Int = 0
    var title = "MBOX"
}

enum TestPattern {
    static let maxSide = 16384

    static func render(_ spec: TestPatternSpec) -> CGImage? {
        let w = spec.width, h = spec.height
        guard w >= 32, h >= 32, w <= maxSide, h <= maxSide,
              let cs = CGColorSpace(name: CGColorSpace.sRGB),
              let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                                  space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)
        else { return nil }
        // 왼쪽 위가 (0,0)이 되도록 뒤집는다
        ctx.translateBy(x: 0, y: CGFloat(h))
        ctx.scaleBy(x: 1, y: -1)
        Painter(ctx: ctx, spec: spec).draw()
        return ctx.makeImage()
    }

    static func aspectText(_ w: Int, _ h: Int) -> String {
        func gcd(_ a: Int, _ b: Int) -> Int { b == 0 ? a : gcd(b, a % b) }
        let g = gcd(w, h)
        let a = w / g, b = h / g
        if a <= 64 && b <= 64 { return "\(a):\(b)" }
        return String(format: "%.2f:1", Double(w) / Double(h))
    }
}

func writePNG(_ image: CGImage, to url: URL) throws {
    guard let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
        throw NSError(domain: "LEDWallpaperKeeper", code: 1, userInfo: [NSLocalizedDescriptionKey: "파일을 만들 수 없음"])
    }
    CGImageDestinationAddImage(dest, image, nil)
    guard CGImageDestinationFinalize(dest) else {
        throw NSError(domain: "LEDWallpaperKeeper", code: 2, userInfo: [NSLocalizedDescriptionKey: "PNG 저장 실패"])
    }
}

// MARK: - 그리기

private func rgb(_ hex: UInt32, _ alpha: CGFloat = 1) -> CGColor {
    CGColor(srgbRed: CGFloat((hex >> 16) & 0xFF) / 255,
            green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255, alpha: alpha)
}

private struct Palette {
    static let bg = rgb(0x05060A)
    static let bgCenter = rgb(0x0D1119)
    static let gridMinor = rgb(0x151922)
    static let gridCabinet = rgb(0x2A3140)
    static let diagonal = rgb(0x1E2430)
    static let ringDim = rgb(0x2A3142)
    static let cyan = rgb(0x00D8FF)
    static let magenta = rgb(0xFF2E88)
    static let text = rgb(0xFFFFFF)
    static let textDim = rgb(0x7D879A)
    static let label = rgb(0x8A93A6)
}

private struct Painter {
    let ctx: CGContext
    let spec: TestPatternSpec
    let W: CGFloat
    let H: CGFloat
    let iw: Int
    let ih: Int
    let unit: CGFloat      // min(W,H)
    let margin: CGFloat
    let bandH: CGFloat
    let center: CGPoint
    let radius: CGFloat

    init(ctx: CGContext, spec: TestPatternSpec) {
        self.ctx = ctx
        self.spec = spec
        iw = spec.width
        ih = spec.height
        W = CGFloat(spec.width)
        H = CGFloat(spec.height)
        unit = min(W, H)
        margin = (unit * 0.06).rounded()
        bandH = (unit * 0.075).rounded()
        center = CGPoint(x: W / 2, y: H / 2)
        let gap = unit * 0.035
        radius = max(unit * 0.12, min(unit * 0.37, H / 2 - margin - bandH - gap, W / 2 - margin))
    }

    func draw() {
        background()
        grid()
        diagonals()
        centerLines()
        sideCircles()
        bands()
        pixelPatches()
        mainDisc()
        edgeMarks()
    }

    // MARK: 배경, 그리드

    private func background() {
        ctx.setFillColor(Palette.bg)
        ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))
        let g = CGGradient(colorsSpace: nil, colors: [Palette.bgCenter, Palette.bg] as CFArray, locations: [0, 1])!
        ctx.drawRadialGradient(g, startCenter: center, startRadius: 0, endCenter: center,
                               endRadius: hypot(W, H) * 0.55, options: [.drawsAfterEndLocation])
    }

    private func vLine(_ x: Int, _ color: CGColor) {
        ctx.setFillColor(color)
        ctx.fill(CGRect(x: x, y: 0, width: 1, height: ih))
    }

    private func hLine(_ y: Int, _ color: CGColor) {
        ctx.setFillColor(color)
        ctx.fill(CGRect(x: 0, y: y, width: iw, height: 1))
    }

    private func grid() {
        ctx.setShouldAntialias(false)
        defer { ctx.setShouldAntialias(true) }
        if spec.cabinetW > 0 && spec.cabinetH > 0 {
            let cw = spec.cabinetW, ch = spec.cabinetH
            for x in stride(from: cw, to: iw, by: cw) { vLine(x, Palette.gridCabinet) }
            for y in stride(from: ch, to: ih, by: ch) { hLine(y, Palette.gridCabinet) }
            let cols = (iw + cw - 1) / cw, rows = (ih + ch - 1) / ch
            guard cols * rows <= 4000 else { return }
            let size = max(7, min(CGFloat(min(cw, ch)) * 0.1, unit * 0.017))
            let font = NSFont.monospacedSystemFont(ofSize: size, weight: .medium)
            ctx.setShouldAntialias(true)
            for r in 0..<rows {
                for c in 0..<cols {
                    // 네 모서리 칸은 좌표 표기와 겹치므로 생략
                    if (r == 0 || r == rows - 1) && (c == 0 || c == cols - 1) { continue }
                    text("\(c + 1)-\(r + 1)", font: font, color: Palette.label,
                         at: CGPoint(x: CGFloat(c * cw) + size * 0.5, y: CGFloat(r * ch) + size * 0.5), anchor: .topLeft)
                }
            }
        } else {
            let cell = max(8, Int((unit / 8 / 8).rounded()) * 8)
            for x in stride(from: cell, to: iw, by: cell) { vLine(x, Palette.gridMinor) }
            for y in stride(from: cell, to: ih, by: cell) { hLine(y, Palette.gridMinor) }
        }
    }

    private func diagonals() {
        ctx.setStrokeColor(Palette.diagonal)
        ctx.setLineWidth(1)
        ctx.move(to: .zero); ctx.addLine(to: CGPoint(x: W, y: H))
        ctx.move(to: CGPoint(x: W, y: 0)); ctx.addLine(to: CGPoint(x: 0, y: H))
        ctx.strokePath()
    }

    private func centerLines() {
        ctx.setShouldAntialias(false)
        vLine(iw / 2, rgb(0x00D8FF, 0.28))
        hLine(ih / 2, rgb(0x00D8FF, 0.28))
        ctx.setShouldAntialias(true)
    }

    // MARK: 좌우 원 (가로로 긴 화면에서 비율 확인용)

    private func sideCircles() {
        let inner = W / 2 - radius
        let r2 = min(radius * 0.62, (inner - margin) / 2 - unit * 0.04)
        guard r2 > unit * 0.12 else { return }
        let cxL = (margin + inner) / 2
        for (i, cx) in [cxL, W - cxL].enumerated() {
            let c = CGPoint(x: cx, y: H / 2)
            ctx.setFillColor(rgb(0x07090E))
            ctx.fillEllipse(in: CGRect(x: c.x - r2, y: c.y - r2, width: r2 * 2, height: r2 * 2))
            ctx.setStrokeColor(Palette.ringDim)
            ctx.setLineWidth(max(1, unit * 0.002))
            ctx.strokeEllipse(in: CGRect(x: c.x - r2, y: c.y - r2, width: r2 * 2, height: r2 * 2))
            ctx.strokeEllipse(in: CGRect(x: c.x - r2 * 0.66, y: c.y - r2 * 0.66, width: r2 * 1.32, height: r2 * 1.32))
            ticks(center: c, r: r2, count: 24, len: r2 * 0.06, major: 6, color: Palette.ringDim, majorColor: Palette.cyan)
            // 가운데 십자
            ctx.setStrokeColor(Palette.cyan)
            ctx.setLineWidth(max(1, unit * 0.0025))
            let k = r2 * 0.12
            ctx.move(to: CGPoint(x: c.x - k, y: c.y)); ctx.addLine(to: CGPoint(x: c.x + k, y: c.y))
            ctx.move(to: CGPoint(x: c.x, y: c.y - k)); ctx.addLine(to: CGPoint(x: c.x, y: c.y + k))
            ctx.strokePath()
            let f = NSFont.monospacedSystemFont(ofSize: r2 * 0.1, weight: .semibold)
            text(i == 0 ? "L" : "R", font: f, color: Palette.textDim, at: CGPoint(x: c.x, y: c.y + r2 * 0.4), anchor: .center)
        }
    }

    // MARK: 위 그레이 / 아래 컬러 띠

    private var bandRectTop: CGRect {
        let x0 = margin + bandH + unit * 0.015
        return CGRect(x: x0, y: margin, width: W - x0 * 2, height: bandH)
    }

    private var bandRectBottom: CGRect {
        var r = bandRectTop
        r.origin.y = H - margin - bandH
        return r
    }

    private func bands() {
        ctx.setShouldAntialias(false)
        defer { ctx.setShouldAntialias(true) }
        // 위: 11단계 그레이 + 부드러운 그라데이션
        let top = bandRectTop
        let stepH = (top.height * 0.62).rounded()
        let steps = 11
        for i in 0..<steps {
            let x0 = (top.minX + top.width * CGFloat(i) / CGFloat(steps)).rounded()
            let x1 = (top.minX + top.width * CGFloat(i + 1) / CGFloat(steps)).rounded()
            let v = CGFloat(i) / CGFloat(steps - 1)
            ctx.setFillColor(CGColor(srgbRed: v, green: v, blue: v, alpha: 1))
            ctx.fill(CGRect(x: x0, y: top.minY, width: x1 - x0, height: stepH))
        }
        gradient(in: CGRect(x: top.minX, y: top.minY + stepH, width: top.width, height: top.height - stepH),
                 colors: [rgb(0x000000), rgb(0xFFFFFF)])
        // 아래: 컬러바 + 색상환 그라데이션
        let bot = bandRectBottom
        let bars: [UInt32] = [0xFFFFFF, 0xFFFF00, 0x00FFFF, 0x00FF00, 0xFF00FF, 0xFF0000, 0x0000FF, 0x000000]
        for (i, hex) in bars.enumerated() {
            let x0 = (bot.minX + bot.width * CGFloat(i) / CGFloat(bars.count)).rounded()
            let x1 = (bot.minX + bot.width * CGFloat(i + 1) / CGFloat(bars.count)).rounded()
            ctx.setFillColor(rgb(hex))
            ctx.fill(CGRect(x: x0, y: bot.minY, width: x1 - x0, height: stepH))
        }
        let hues: [UInt32] = [0xFF0000, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF, 0xFF0000]
        gradient(in: CGRect(x: bot.minX, y: bot.minY + stepH, width: bot.width, height: bot.height - stepH),
                 colors: hues.map { rgb($0) })
        // 테두리
        ctx.setShouldAntialias(true)
        ctx.setStrokeColor(rgb(0x3A4254))
        ctx.setLineWidth(1)
        ctx.stroke(top.insetBy(dx: -0.5, dy: -0.5))
        ctx.stroke(bot.insetBy(dx: -0.5, dy: -0.5))
        // 그레이 퍼센트 표기
        let f = NSFont.monospacedSystemFont(ofSize: max(7, stepH * 0.3), weight: .semibold)
        for i in 0..<steps {
            let cx = top.minX + top.width * (CGFloat(i) + 0.5) / CGFloat(steps)
            let col = i < 6 ? rgb(0xFFFFFF, 0.75) : rgb(0x000000, 0.75)
            text("\(i * 10)", font: f, color: col, at: CGPoint(x: cx, y: top.minY + stepH / 2), anchor: .center)
        }
    }

    private func gradient(in rect: CGRect, colors: [CGColor]) {
        let locs = (0..<colors.count).map { CGFloat($0) / CGFloat(colors.count - 1) }
        guard let g = CGGradient(colorsSpace: CGColorSpace(name: CGColorSpace.sRGB), colors: colors as CFArray, locations: locs)
        else { return }
        ctx.saveGState()
        ctx.clip(to: rect)
        ctx.drawLinearGradient(g, start: CGPoint(x: rect.minX, y: 0), end: CGPoint(x: rect.maxX, y: 0), options: [])
        ctx.restoreGState()
    }

    // MARK: 1픽셀 확인 패치 (띠 양끝)

    private func pixelPatches() {
        ctx.setShouldAntialias(false)
        defer { ctx.setShouldAntialias(true) }
        let p = Int(bandH)
        let left = Int(margin)
        let right = iw - Int(margin) - p
        let topY = Int(margin)
        let botY = ih - Int(margin) - p
        patch(x: left, y: topY, size: p) { x, y in (x + y) % 2 == 0 }          // 1px 체커
        patch(x: right, y: topY, size: p) { x, _ in x % 2 == 0 }               // 1px 세로줄
        patch(x: left, y: botY, size: p) { _, y in y % 2 == 0 }                // 1px 가로줄
        patch(x: right, y: botY, size: p) { x, y in (x / 2 + y / 2) % 2 == 0 } // 2px 체커
    }

    private func patch(x: Int, y: Int, size: Int, on: (Int, Int) -> Bool) {
        ctx.setFillColor(rgb(0x000000))
        ctx.fill(CGRect(x: x, y: y, width: size, height: size))
        ctx.setFillColor(rgb(0xFFFFFF))
        for yy in 0..<size {
            var runStart = -1
            for xx in 0...size {
                let lit = xx < size && on(xx, yy)
                if lit && runStart < 0 { runStart = xx }
                if !lit && runStart >= 0 {
                    ctx.fill(CGRect(x: x + runStart, y: y + yy, width: xx - runStart, height: 1))
                    runStart = -1
                }
            }
        }
    }

    // MARK: 가운데 원 + 로고

    private func ticks(center c: CGPoint, r: CGFloat, count: Int, len: CGFloat, major: Int,
                       color: CGColor, majorColor: CGColor) {
        for i in 0..<count {
            let a = CGFloat(i) / CGFloat(count) * .pi * 2 - .pi / 2
            let isMajor = i % major == 0
            let l = isMajor ? len * 2 : len
            let p0 = CGPoint(x: c.x + cos(a) * (r - l), y: c.y + sin(a) * (r - l))
            let p1 = CGPoint(x: c.x + cos(a) * r, y: c.y + sin(a) * r)
            ctx.setStrokeColor(isMajor ? majorColor : color)
            ctx.setLineWidth(max(1, unit * (isMajor ? 0.003 : 0.0018)))
            ctx.move(to: p0); ctx.addLine(to: p1)
            ctx.strokePath()
        }
    }

    private func mainDisc() {
        let r = radius, c = center
        let disc = CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)
        // 원 안 채우기
        ctx.saveGState()
        ctx.addEllipse(in: disc)
        ctx.clip()
        let g = CGGradient(colorsSpace: nil, colors: [rgb(0x121826), rgb(0x06080D)] as CFArray, locations: [0, 1])!
        ctx.drawRadialGradient(g, startCenter: CGPoint(x: c.x, y: c.y - r * 0.3), startRadius: 0,
                               endCenter: c, endRadius: r, options: [.drawsAfterEndLocation])
        ctx.restoreGState()

        // 바깥 링: 시안 → 마젠타 그라데이션
        let ringW = max(2, unit * 0.006)
        ctx.saveGState()
        ctx.setLineWidth(ringW)
        ctx.addEllipse(in: disc.insetBy(dx: ringW / 2, dy: ringW / 2))
        ctx.replacePathWithStrokedPath()
        ctx.clip()
        let rg = CGGradient(colorsSpace: nil, colors: [Palette.cyan, Palette.magenta] as CFArray, locations: [0, 1])!
        ctx.drawLinearGradient(rg, start: CGPoint(x: disc.minX, y: disc.minY), end: CGPoint(x: disc.maxX, y: disc.maxY), options: [])
        ctx.restoreGState()

        // 안쪽 얇은 링 + 눈금
        ctx.setStrokeColor(Palette.ringDim)
        ctx.setLineWidth(max(1, unit * 0.0018))
        let r2 = r * 0.9
        ctx.strokeEllipse(in: CGRect(x: c.x - r2, y: c.y - r2, width: r2 * 2, height: r2 * 2))
        ticks(center: c, r: r * 0.965, count: 72, len: r * 0.025, major: 6, color: rgb(0x3A4254), majorColor: rgb(0xC9F6FF))

        // 로고
        var fs = r * 0.44
        var logo = NSFont.systemFont(ofSize: fs, weight: .black)
        var logoW = measure(spec.title, font: logo, kern: fs * 0.06).width
        if logoW > r * 1.45 {
            fs *= r * 1.45 / logoW
            logo = NSFont.systemFont(ofSize: fs, weight: .black)
            logoW = measure(spec.title, font: logo, kern: fs * 0.06).width
        }
        let logoY = c.y - r * 0.12
        // 은은한 글로우
        ctx.saveGState()
        ctx.setShadow(offset: .zero, blur: fs * 0.35, color: rgb(0x00D8FF, 0.45))
        text(spec.title, font: logo, color: Palette.text, kern: fs * 0.06, at: CGPoint(x: c.x, y: logoY), anchor: .center)
        ctx.restoreGState()
        text(spec.title, font: logo, color: Palette.text, kern: fs * 0.06, at: CGPoint(x: c.x, y: logoY), anchor: .center)

        // 로고 아래 그라데이션 선
        let lineY = logoY + fs * 0.52
        let lineW = logoW * 0.78
        let lineRect = CGRect(x: c.x - lineW / 2, y: lineY, width: lineW, height: max(2, fs * 0.035))
        gradient(in: lineRect, colors: [rgb(0x00D8FF, 0), Palette.cyan, Palette.magenta, rgb(0xFF2E88, 0)])

        // 부제, 해상도
        let sub = NSFont.systemFont(ofSize: fs * 0.13, weight: .semibold)
        text("LED  TEST  PATTERN", font: sub, color: Palette.cyan, kern: fs * 0.045,
             at: CGPoint(x: c.x, y: lineY + fs * 0.22), anchor: .center)
        let mono = NSFont.monospacedSystemFont(ofSize: fs * 0.15, weight: .bold)
        text("\(iw) × \(ih) PX", font: mono, color: Palette.text, kern: fs * 0.01,
             at: CGPoint(x: c.x, y: lineY + fs * 0.47), anchor: .center)
        let mp = Double(iw * ih) / 1_000_000
        let monoS = NSFont.monospacedSystemFont(ofSize: fs * 0.1, weight: .medium)
        var info = "\(TestPattern.aspectText(iw, ih))  ·  \(String(format: "%.2f", mp)) MP"
        if spec.cabinetW > 0 && spec.cabinetH > 0 {
            let cols = (iw + spec.cabinetW - 1) / spec.cabinetW, rows = (ih + spec.cabinetH - 1) / spec.cabinetH
            info += "  ·  CAB \(spec.cabinetW)×\(spec.cabinetH) (\(cols)×\(rows))"
        }
        text(info, font: monoS, color: Palette.textDim, at: CGPoint(x: c.x, y: lineY + fs * 0.67), anchor: .center)

        // 로고 위 작은 점 + 표기
        let dotY = logoY - fs * 0.62
        let d = fs * 0.05
        let sigFont = NSFont.monospacedSystemFont(ofSize: fs * 0.085, weight: .semibold)
        let sigW = measure("SIGNAL CHECK", font: sigFont, kern: fs * 0.02).width
        let gapDot = d * 1.6
        let startX = c.x - (sigW + d + gapDot) / 2
        ctx.setFillColor(Palette.magenta)
        ctx.fillEllipse(in: CGRect(x: startX, y: dotY - d / 2, width: d, height: d))
        text("SIGNAL CHECK", font: sigFont, color: Palette.label, kern: fs * 0.02,
             at: CGPoint(x: startX + d + gapDot, y: dotY - sigFont.capHeight / 2), anchor: .topLeft)
    }

    // MARK: 가장자리 표시

    private func edgeMarks() {
        // 1px 흰 테두리 (실제 화면 끝 확인)
        ctx.setShouldAntialias(false)
        ctx.setFillColor(rgb(0xFFFFFF))
        ctx.fill(CGRect(x: 0, y: 0, width: iw, height: 1))
        ctx.fill(CGRect(x: 0, y: ih - 1, width: iw, height: 1))
        ctx.fill(CGRect(x: 0, y: 0, width: 1, height: ih))
        ctx.fill(CGRect(x: iw - 1, y: 0, width: 1, height: ih))
        // 모서리 ㄱ자 마커
        let L = Int(unit * 0.045), t = max(2, Int(unit * 0.005))
        let inset = max(3, Int(unit * 0.012))
        ctx.setFillColor(Palette.magenta)
        for (cx, sx) in [(inset, 1), (iw - inset, -1)] {
            for (cy, sy) in [(inset, 1), (ih - inset, -1)] {
                let hx = sx > 0 ? cx : cx - L
                let vy = sy > 0 ? cy : cy - L
                ctx.fill(CGRect(x: hx, y: sy > 0 ? cy : cy - t, width: L, height: t))
                ctx.fill(CGRect(x: sx > 0 ? cx : cx - t, y: vy, width: t, height: L))
            }
        }
        ctx.setShouldAntialias(true)
        // 모서리 좌표
        let f = NSFont.monospacedSystemFont(ofSize: max(8, unit * 0.017), weight: .medium)
        let o = CGFloat(inset + t) + unit * 0.012
        text("0,0", font: f, color: Palette.label, at: CGPoint(x: o, y: o), anchor: .topLeft)
        text("\(iw - 1),0", font: f, color: Palette.label, at: CGPoint(x: W - o, y: o), anchor: .topRight)
        text("0,\(ih - 1)", font: f, color: Palette.label, at: CGPoint(x: o, y: H - o), anchor: .bottomLeft)
        text("\(iw - 1),\(ih - 1)", font: f, color: Palette.label, at: CGPoint(x: W - o, y: H - o), anchor: .bottomRight)
        // 각 변 가운데 삼각형
        let s = unit * 0.022
        ctx.setFillColor(rgb(0xFFFFFF))
        let mid = [
            (CGPoint(x: W / 2, y: 1), CGPoint(x: 0, y: 1)),
            (CGPoint(x: W / 2, y: H - 1), CGPoint(x: 0, y: -1)),
            (CGPoint(x: 1, y: H / 2), CGPoint(x: 1, y: 0)),
            (CGPoint(x: W - 1, y: H / 2), CGPoint(x: -1, y: 0)),
        ]
        for (p, n) in mid {
            let tip = CGPoint(x: p.x + n.x * s, y: p.y + n.y * s)
            let px = CGPoint(x: -n.y, y: n.x)
            ctx.move(to: CGPoint(x: p.x + px.x * s * 0.7, y: p.y + px.y * s * 0.7))
            ctx.addLine(to: tip)
            ctx.addLine(to: CGPoint(x: p.x - px.x * s * 0.7, y: p.y - px.y * s * 0.7))
            ctx.closePath()
        }
        ctx.fillPath()
    }

    // MARK: 글자

    enum Anchor { case center, topLeft, topRight, bottomLeft, bottomRight }

    private func line(_ s: String, font: NSFont, color: CGColor, kern: CGFloat) -> CTLine {
        let attrs: [NSAttributedString.Key: Any] = [
            NSAttributedString.Key(kCTFontAttributeName as String): font,
            NSAttributedString.Key(kCTForegroundColorAttributeName as String): color,
            NSAttributedString.Key(kCTKernAttributeName as String): kern,
        ]
        return CTLineCreateWithAttributedString(NSAttributedString(string: s, attributes: attrs))
    }

    private func measure(_ s: String, font: NSFont, kern: CGFloat = 0) -> CGSize {
        let l = line(s, font: font, color: Palette.text, kern: kern)
        var a: CGFloat = 0, d: CGFloat = 0, lead: CGFloat = 0
        let w = CGFloat(CTLineGetTypographicBounds(l, &a, &d, &lead)) - kern
        return CGSize(width: w, height: a + d)
    }

    private func text(_ s: String, font: NSFont, color: CGColor, kern: CGFloat = 0, at p: CGPoint, anchor: Anchor) {
        let l = line(s, font: font, color: color, kern: kern)
        var a: CGFloat = 0, d: CGFloat = 0, lead: CGFloat = 0
        let w = CGFloat(CTLineGetTypographicBounds(l, &a, &d, &lead)) - kern
        // 대문자 높이 기준으로 세로 가운데 맞춤
        let capH = font.capHeight
        let x: CGFloat
        let baseline: CGFloat
        switch anchor {
        case .center: x = p.x - w / 2; baseline = p.y + capH / 2
        case .topLeft: x = p.x; baseline = p.y + capH
        case .topRight: x = p.x - w; baseline = p.y + capH
        case .bottomLeft: x = p.x; baseline = p.y
        case .bottomRight: x = p.x - w; baseline = p.y
        }
        ctx.saveGState()
        ctx.textMatrix = .identity
        ctx.translateBy(x: x, y: baseline)
        ctx.scaleBy(x: 1, y: -1)
        ctx.textPosition = .zero
        CTLineDraw(l, ctx)
        ctx.restoreGState()
    }
}

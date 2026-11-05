import AppKit
import SwiftUI

private let brandCyan = Color(red: 0, green: 0.85, blue: 1)
private let brandPink = Color(red: 1, green: 0.18, blue: 0.53)

/// 메인 창. 닫아도 앱은 메뉴바에 남는다.
struct MainView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider()
            HStack(alignment: .top, spacing: 16) {
                wallpaperCard.frame(width: 300)
                patternCard
            }
            .padding(16)
            Divider()
            footer
        }
        .frame(width: 900)
        .fixedSize(horizontal: false, vertical: true)
    }

    // MARK: 머리

    private var header: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 9, style: .continuous)
                    .fill(LinearGradient(colors: [brandCyan, brandPink], startPoint: .topLeading, endPoint: .bottomTrailing))
                Image(systemName: "display.2")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(.white)
            }
            .frame(width: 36, height: 36)
            VStack(alignment: .leading, spacing: 2) {
                Text("MBOX LED Tools").font(.system(size: 16, weight: .bold))
                Text("바탕화면 백업 · 테스트패턴").font(.system(size: 12)).foregroundStyle(.secondary)
            }
            Spacer()
            if !model.showingOn.isEmpty {
                pill("표출 중 · \(model.showingOn.count)", color: brandPink)
            }
            if !model.hasScreenPermission {
                Button {
                    model.requestPermission()
                } label: {
                    Label("화면 기록 권한 필요", systemImage: "exclamationmark.triangle.fill")
                }
                .buttonStyle(.bordered)
                .tint(.orange)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }

    private func pill(_ text: String, color: Color) -> some View {
        HStack(spacing: 6) {
            Circle().fill(color).frame(width: 7, height: 7)
            Text(text).font(.system(size: 12, weight: .semibold))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(color.opacity(0.14), in: Capsule())
    }

    // MARK: 바탕화면 백업

    private var wallpaperCard: some View {
        Card(title: "바탕화면 백업", icon: "photo.on.rectangle.angled") {
            Text("누르는 순간 외부 디스플레이 화면을 캡처해서 그 디스플레이의 바탕화면으로 바꿔요. 재생 프로그램이 튕기면 이 화면이 남아요.")
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            VStack(spacing: 0) {
                if model.externalDisplays.isEmpty {
                    Text("연결된 외부 디스플레이가 없어요")
                        .font(.system(size: 12))
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10)
                }
                ForEach(Array(model.externalDisplays.enumerated()), id: \.element.id) { i, d in
                    if i > 0 { Divider().padding(.leading, 38) }
                    HStack(spacing: 10) {
                        Image(systemName: "display")
                            .font(.system(size: 15))
                            .foregroundStyle(model.isEnabled(d) ? brandCyan : .secondary)
                            .frame(width: 18)
                        VStack(alignment: .leading, spacing: 1) {
                            Text(d.name).font(.system(size: 13, weight: .medium)).lineLimit(1)
                            Text(d.sizeText).font(.system(size: 11, design: .monospaced)).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Toggle("", isOn: Binding(get: { model.isEnabled(d) }, set: { model.setEnabled(d, $0) }))
                            .toggleStyle(.switch)
                            .controlSize(.small)
                            .labelsHidden()
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                }
            }
            .background(Color.primary.opacity(0.04), in: RoundedRectangle(cornerRadius: 8, style: .continuous))

            Button {
                Task { await model.captureAll() }
            } label: {
                Label(model.isCapturing ? "캡처 중…" : "지금 캡처 → 바탕화면 교체", systemImage: "camera.viewfinder")
                    .font(.system(size: 13, weight: .semibold))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(model.isCapturing || model.externalDisplays.isEmpty)

            HStack(spacing: 6) {
                Image(systemName: "clock").font(.system(size: 11))
                Text(model.captureStatus).font(.system(size: 11)).lineLimit(2)
            }
            .foregroundStyle(.secondary)

            Text("메인 모니터는 건드리지 않아요.")
                .font(.system(size: 11))
                .foregroundStyle(.tertiary)
        }
    }

    // MARK: 테스트패턴

    private var patternCard: some View {
        Card(title: "테스트패턴", icon: "square.grid.3x3.fill") {
            HStack {
                Picker("", selection: $model.style) {
                    ForEach(TestPatternStyle.selectable, id: \.self) { Text($0.label).tag($0) }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
                .frame(width: 180)
                Spacer()
                Text(model.sizeSummary)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            ZStack {
                RoundedRectangle(cornerRadius: 8, style: .continuous).fill(Color.black)
                if let img = model.preview {
                    Image(nsImage: img)
                        .resizable()
                        .interpolation(.high)
                        .aspectRatio(contentMode: .fit)
                        .padding(6)
                } else {
                    Text("크기를 확인해 주세요").foregroundStyle(.secondary)
                }
            }
            .frame(height: 190)
            .overlay(RoundedRectangle(cornerRadius: 8, style: .continuous).stroke(Color.primary.opacity(0.12)))

            Grid(alignment: .leading, horizontalSpacing: 10, verticalSpacing: 10) {
                GridRow {
                    rowLabel("크기")
                    HStack(spacing: 6) {
                        numberField("가로", $model.widthText)
                        Text("×").foregroundStyle(.secondary)
                        numberField("세로", $model.heightText)
                        Text("px").foregroundStyle(.secondary)
                        Menu {
                            ForEach(AppModel.presets, id: \.0) { p in
                                Button(p.0) { model.applyPreset(p.1, p.2) }
                            }
                            Divider()
                            Button("표출할 디스플레이 해상도로") { model.useTargetDisplaySize() }
                        } label: {
                            Text("자주 쓰는 크기")
                        }
                        .fixedSize()
                    }
                }
                GridRow {
                    rowLabel("캐비닛")
                    HStack(spacing: 6) {
                        numberField("없음", $model.cabWText)
                        Text("×").foregroundStyle(.secondary)
                        numberField("없음", $model.cabHText)
                        Text("px · 비우면 선 없음").foregroundStyle(.secondary).font(.system(size: 11))
                    }
                }
                GridRow {
                    rowLabel("표출")
                    HStack(spacing: 8) {
                        Picker("", selection: $model.targetID) {
                            ForEach(model.displays) { d in
                                Text("\(d.name)\(d.isMain ? " (메인)" : "") · \(d.sizeText)").tag(d.id)
                            }
                        }
                        .labelsHidden()
                        .frame(width: 250)
                        Picker("", selection: $model.placement) {
                            ForEach(Placement.allCases) { Text($0.label).tag($0) }
                        }
                        .pickerStyle(.segmented)
                        .labelsHidden()
                    }
                }
            }
            .font(.system(size: 12))

            HStack(spacing: 10) {
                Button {
                    model.savePNG()
                } label: {
                    Label("PNG 저장", systemImage: "square.and.arrow.down").frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
                .disabled(model.currentSpec == nil)

                Button {
                    model.showPattern()
                } label: {
                    Label("바로 표출", systemImage: "play.rectangle.fill").frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(brandPink)
                .controlSize(.large)
                .disabled(model.currentSpec == nil || model.targetID.isEmpty)

                if !model.showingOn.isEmpty {
                    Button {
                        model.hideAll()
                    } label: {
                        Label("표출 끄기", systemImage: "stop.fill").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.large)
                }
            }

            if !model.patternMessage.isEmpty {
                Text(model.patternMessage).font(.system(size: 11)).foregroundStyle(.secondary)
            }
        }
    }

    private func rowLabel(_ s: String) -> some View {
        Text(s).foregroundStyle(.secondary).frame(width: 44, alignment: .leading)
    }

    private func numberField(_ placeholder: String, _ text: Binding<String>) -> some View {
        TextField(placeholder, text: text)
            .textFieldStyle(.roundedBorder)
            .multilineTextAlignment(.trailing)
            .font(.system(size: 12, design: .monospaced))
            .frame(width: 66)
    }

    // MARK: 아래

    private var footer: some View {
        HStack(spacing: 14) {
            Toggle("로그인할 때 자동 실행", isOn: $model.launchAtLogin)
                .toggleStyle(.checkbox)
            Spacer()
            Text("창을 닫아도 상단 메뉴바에서 계속 쓸 수 있어요")
                .foregroundStyle(.tertiary)
            Button {
                model.openFolder()
            } label: {
                Label("캡처 폴더", systemImage: "folder")
            }
            .buttonStyle(.borderless)
            Button("종료") { NSApp.terminate(nil) }
                .buttonStyle(.borderless)
        }
        .font(.system(size: 12))
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
    }
}

/// 둥근 카드
private struct Card<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label(title, systemImage: icon)
                .font(.system(size: 14, weight: .bold))
            content
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).stroke(Color.primary.opacity(0.08)))
    }
}

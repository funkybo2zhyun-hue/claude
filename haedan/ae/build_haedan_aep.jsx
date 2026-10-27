// 대전광역시 선수단 해단식 메인 화면 — AE 프로젝트 생성 스크립트
// 실행: After Effects > 파일 > 스크립트 > 스크립트 파일 실행 (또는 AfterFX.exe -r 이 파일)
// 이 파일과 같은 폴더의 assets\ 를 불러와 3072x1728 / 60fps / 20초 컴프를 만들고 .aep 로 저장한다.
// 글자는 전부 텍스트 레이어라서 문자 도구로 바로 고치면 된다. 금색은 "메인타이틀" 텍스트를 매트로 쓰는 그라데이션 솔리드.
(function () {
    var here = File($.fileName).parent;
    var A = here.fullName + "/assets/";
    var W = 3072, H = 1728, FPS = 60, DUR = 20;
    var DX = -3; // 원본 아트보드(3078)에서 좌우 3px씩 잘라 3072로 맞춤

    app.beginUndoGroup("해단식 메인");
    app.newProject();
    var proj = app.project;

    function imp(name) {
        var io = new ImportOptions(File(A + name));
        return proj.importFile(io);
    }
    function font(cands) {
        // 설치된 폰트 중 첫 번째로 찾은 PostScript 이름
        try {
            for (var i = 0; i < cands.length; i++) {
                var f = app.fonts.getFontsByPostScriptName(cands[i]);
                if (f && f.length) return cands[i];
            }
        } catch (e) {}
        return cands[0];
    }
    var GMARKET = font(["GmarketSansBold", "GmarketSansTTFBold"]);
    var DREAM6 = font(["S-CoreDream-6Bold", "SCDream6"]);

    var fBG = imp("BG_loop_v2_3072x1728_20s_60fps.mp4");
    fBG.mainSource.loop = 50;
    var fLogo1 = imp("logo_daejeon@2x.png");
    var fLogo2 = imp("logo_worldskills_committee@2x.png");

    var comp = proj.items.addComp("해단식_메인_3072x1728", W, H, 1, DUR, FPS);
    comp.bgColor = [0, 0, 0];

    function hexc(h) { return [parseInt(h.substr(0, 2), 16) / 255, parseInt(h.substr(2, 2), 16) / 255, parseInt(h.substr(4, 2), 16) / 255]; }
    function addText(name, str, fnt, size, color, x, baseY, just, tracking) {
        var l = comp.layers.addText(str);
        l.name = name;
        var p = l.property("Source Text");
        var d = p.value;
        d.resetCharStyle(); d.resetParagraphStyle();
        d.font = fnt; d.fontSize = size; d.fillColor = color; d.applyFill = true; d.applyStroke = false;
        d.tracking = tracking || 0;
        d.justification = just;
        p.setValue(d);
        l.property("Position").setValue([x + DX, baseY]);
        return l;
    }
    function ease(prop) {
        var e = new KeyframeEase(0, 40);
        for (var k = 1; k <= prop.numKeys; k++) {
            if (prop.keyOutInterpolationType(k) != KeyframeInterpolationType.HOLD) {
                var dims = prop.value instanceof Array ? prop.value.length : 1;
                if (prop.propertyValueType == PropertyValueType.TwoD_SPATIAL || prop.propertyValueType == PropertyValueType.ThreeD_SPATIAL) dims = 1;
                var arr = []; for (var j = 0; j < dims; j++) arr.push(e);
                prop.setTemporalEaseAtKey(k, arr, arr);
            }
        }
    }

    // 1) 배경 루프
    var bg = comp.layers.add(fBG);
    bg.name = "배경 루프 (v2)";
    bg.outPoint = DUR;

    // 2) 로고 이미지 (원본 그대로)
    var lg1 = comp.layers.add(fLogo1); lg1.name = "로고_대전광역시";
    lg1.property("Scale").setValue([50, 50]); lg1.property("Position").setValue([1348 + DX, 981.5]);
    var lg2 = comp.layers.add(fLogo2); lg2.name = "로고_월드스킬즈_기능경기위원회";
    lg2.property("Scale").setValue([50, 50]); lg2.property("Position").setValue([2015 + DX, 955.5]);

    // 3) 일시·장소·주최·주관 (에스코어드림 6 Bold, 흰색)
    var WHITE = [1, 1, 1];
    addText("일시", "| 일시 | 2026년 10월 29일(목) 17시", DREAM6, 49, WHITE, 697.2, 882.5, ParagraphJustification.LEFT_JUSTIFY);
    addText("장소", "| 장소 | 롯데시티호텔 1층 크리스탈볼룸", DREAM6, 49, WHITE, 1554.5, 879.3, ParagraphJustification.LEFT_JUSTIFY);
    addText("주최", "| 주최 |", DREAM6, 49, WHITE, 1036.6, 1004.5, ParagraphJustification.LEFT_JUSTIFY);
    addText("주관", "| 주관 |", DREAM6, 49, WHITE, 1553.7, 1004.5, ParagraphJustification.LEFT_JUSTIFY);

    // 4) 대회명 (G마켓 산스 Bold, 흰색) — 아트보드2처럼 빼려면 이 레이어 눈을 끄면 된다
    addText("대회명", "2026 인천광역시 제61회 전국기능경기대회", GMARKET, 112.08, WHITE, 467.6, 480.8, ParagraphJustification.LEFT_JUSTIFY);

    // 5) 메인타이틀: 텍스트(매트) + 금색 그라데이션 + 광택
    var TX = 1534.5 + DX, TY = 685; // G마켓 산스 Bold 200 / 자간 -35 가 원본 금색 글자와 맞음
    var title = addText("메인타이틀 ← 여기서 글자 수정", "대전광역시 선수단 해단식", GMARKET, 200, WHITE, TX, TY, ParagraphJustification.CENTER_JUSTIFY, -35);
    // 앵커를 글자 가운데로 옮겨서 숨쉬기 스케일이 가운데 기준으로 되게
    var r = title.sourceRectAtTime(0, false);
    title.property("Anchor Point").setValue([r.left + r.width / 2, r.top + r.height / 2]);
    title.property("Position").setValue([TX, TY + r.top + r.height / 2]);
    var sc = title.property("Scale");
    sc.setValueAtTime(0, [100, 100]); sc.setValueAtTime(10, [101.5, 101.5]); sc.setValueAtTime(20, [100, 100]);
    ease(sc);

    var gold = comp.layers.addSolid([1, 1, 1], "금색 그라데이션", W, H, 1, DUR);
    var ramp = gold.property("Effects").addProperty("ADBE Ramp");
    ramp.property(1).setValue([480 + DX, 540]);          // 시작점 (왼쪽, 어두운 금색)
    ramp.property(2).setValue(hexc("A98C57"));
    ramp.property(3).setValue([2150 + DX, 700]);         // 끝점 (오른쪽, 밝은 금색)
    ramp.property(4).setValue(hexc("EFE3BF"));
    // (Glow 제거: 전체 화면 솔리드라 금색이 흰색으로 날아감)

    var shine = comp.layers.addSolid([1, 0.97, 0.88], "광택 (지나가는 빛)", 220, 700, 1, DUR);
    shine.blendingMode = BlendingMode.ADD;
    shine.property("Opacity").setValue(70);
    shine.property("Rotation").setValue(20);
    var blur = shine.property("Effects").addProperty("ADBE Gaussian Blur 2");
    blur.property(1).setValue(60);
    var sp = shine.property("Position");
    var y = TY - 90;
    sp.setValueAtTime(0, [200, y]); sp.setValueAtTime(2, [200, y]); sp.setValueAtTime(4, [2900, y]);
    sp.setValueAtTime(12, [200, y]); sp.setValueAtTime(14, [2900, y]); sp.setValueAtTime(20, [2900, y]);
    // 2→4초, 12→14초에 한 번씩 지나가고 나머지는 글자 밖에 멈춤
    for (var k = 1; k <= sp.numKeys; k++) {
        var t = sp.keyTime(k);
        var hold = (t == 0 || t == 4 || t == 14 || t == 20);
        sp.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, hold ? KeyframeInterpolationType.HOLD : KeyframeInterpolationType.LINEAR);
    }
    ease(sp);

    // 순서: 광택 > 금색 > 텍스트 (텍스트가 둘의 알파 매트)
    gold.moveBefore(title); shine.moveBefore(gold);
    var TM = (typeof TrackMatteType !== "undefined") ? TrackMatteType.ALPHA : null;
    if (gold.setTrackMatte) {
        gold.setTrackMatte(title, TrackMatteType.ALPHA);
        shine.setTrackMatte(title, TrackMatteType.ALPHA);
        title.enabled = false;
    } else {
        alert("이 버전은 트랙 매트 공유를 지원하지 않습니다 (AE 2023 이상 필요).");
    }

    // 렌더 대기열 (H.264 템플릿이 있으면 사용)
    var rq = proj.renderQueue.items.add(comp);
    var om = rq.outputModule(1);
    try { om.applyTemplate("H.264 - Match Render Settings - 40 Mbps"); } catch (e) {}
    om.file = File(here.fullName + "/render/해단식_메인_3072x1728_20s_60fps");

    app.endUndoGroup();
    Folder(here.fullName + "/render").create();
    proj.save(File(here.fullName + "/해단식_메인_3072x1728.aep"));

    // 확인용 프레임
    try {
        comp.saveFrameToPng(3, File(here.fullName + "/render/check_3s.png"));
        comp.saveFrameToPng(8, File(here.fullName + "/render/check_8s.png"));
    } catch (e) {}
    var log = File(here.fullName + "/render/build_log.txt");
    log.open("w"); log.encoding = "UTF-8";
    log.writeln("fonts: " + GMARKET + " / " + DREAM6);
    log.writeln("title rect: " + r.left + "," + r.top + "," + r.width + "," + r.height);
    log.close();
})();

// 대전광역시 선수단 해단식 메인 화면 v3 — AE 프로젝트 생성 스크립트
// 실행: After Effects > 파일 > 스크립트 > 스크립트 파일 실행 (또는 AfterFX.exe -r 이 파일)
// 컴프 2개를 만든다 (3072x1728 / 60fps / 20초 루프):
//   해단식_메인_A_광택반짝임 : 글자는 여기서 고친다 (원본)
//   해단식_메인_B_글자웨이브 : 글자가 A를 자동으로 따라간다 (익스프레션 연결, 모션은 전부 키프레임)
(function () {
    var here = File($.fileName).parent;
    var A = here.fullName + "/assets/";
    var W = 3072, H = 1728, FPS = 60, DUR = 20;
    var DX = -3; // 원본 아트보드(3078)에서 좌우 3px씩 잘라 3072로 맞춤
    var NAME_A = "해단식_메인_A_광택반짝임", NAME_B = "해단식_메인_B_글자웨이브";
    var TITLE = "메인타이틀 ← 여기서 글자 수정";

    app.beginUndoGroup("해단식 메인 v3");
    app.newProject();
    var proj = app.project;

    function imp(name) { return proj.importFile(new ImportOptions(File(A + name))); }
    function font(cands) {
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

    function hexc(h) { return [parseInt(h.substr(0, 2), 16) / 255, parseInt(h.substr(2, 2), 16) / 255, parseInt(h.substr(4, 2), 16) / 255]; }
    var WHITE = [1, 1, 1], WARM = [1, 0.95, 0.82];
    function easeAll(prop) {
        var e = new KeyframeEase(0, 40);
        for (var k = 1; k <= prop.numKeys; k++) {
            if (prop.keyOutInterpolationType(k) == KeyframeInterpolationType.HOLD) continue;
            var dims = prop.value instanceof Array ? prop.value.length : 1;
            if (prop.propertyValueType == PropertyValueType.TwoD_SPATIAL || prop.propertyValueType == PropertyValueType.ThreeD_SPATIAL) dims = 1;
            var arr = []; for (var j = 0; j < dims; j++) arr.push(e);
            prop.setTemporalEaseAtKey(k, arr, arr);
        }
    }

    function build(name, variant) {
        var comp = proj.items.addComp(name, W, H, 1, DUR, FPS);
        comp.bgColor = [0, 0, 0];
        var linkTo = (variant == "B") ? NAME_A : null;

        function addText(lname, str, fnt, size, x, baseY, just, tracking) {
            var l = comp.layers.addText(str);
            l.name = lname;
            var p = l.property("Source Text");
            var d = p.value;
            d.resetCharStyle(); d.resetParagraphStyle();
            d.font = fnt; d.fontSize = size; d.fillColor = WHITE; d.applyFill = true; d.applyStroke = false;
            d.tracking = tracking || 0;
            d.justification = just;
            p.setValue(d);
            l.property("Position").setValue([x + DX, baseY]);
            if (linkTo) p.expression = 'comp("' + linkTo + '").layer("' + lname + '").text.sourceText';
            return l;
        }

        var bg = comp.layers.add(fBG); bg.name = "배경 루프 (v2)"; bg.outPoint = DUR;
        var lg1 = comp.layers.add(fLogo1); lg1.name = "로고_대전광역시";
        lg1.property("Scale").setValue([50, 50]); lg1.property("Position").setValue([1348 + DX, 981.5]);
        var lg2 = comp.layers.add(fLogo2); lg2.name = "로고_월드스킬즈_기능경기위원회";
        lg2.property("Scale").setValue([50, 50]); lg2.property("Position").setValue([2015 + DX, 955.5]);

        addText("일시", "| 일시 | 2026년 10월 29일(목) 17시", DREAM6, 49, 697.2, 882.5, ParagraphJustification.LEFT_JUSTIFY);
        addText("장소", "| 장소 | 롯데시티호텔 1층 크리스탈볼룸", DREAM6, 49, 1554.5, 879.3, ParagraphJustification.LEFT_JUSTIFY);
        addText("주최", "| 주최 |", DREAM6, 49, 1036.6, 1004.5, ParagraphJustification.LEFT_JUSTIFY);
        addText("주관", "| 주관 |", DREAM6, 49, 1553.7, 1004.5, ParagraphJustification.LEFT_JUSTIFY);
        // 아트보드2처럼 빼려면 이 레이어 눈을 끄면 된다
        addText("대회명", "2026 인천광역시 제61회 전국기능경기대회", GMARKET, 112.08, 467.6, 480.8, ParagraphJustification.LEFT_JUSTIFY);

        // 메인타이틀 (금색 그라데이션의 알파 매트)
        var TX = 1534.5 + DX, TY = 685; // G마켓 산스 Bold 200 / 자간 -35 가 원본 금색 글자와 맞음
        var title = addText(TITLE, "대전광역시 선수단 해단식", GMARKET, 200, TX, TY, ParagraphJustification.CENTER_JUSTIFY, -35);

        var gold = comp.layers.addSolid([1, 1, 1], "금색 그라데이션", W, H, 1, DUR);
        var ramp = gold.property("Effects").addProperty("ADBE Ramp");
        ramp.property(1).setValue([480 + DX, 540]);  ramp.property(2).setValue(hexc("A98C57"));
        ramp.property(3).setValue([2150 + DX, 700]); ramp.property(4).setValue(hexc("EFE3BF"));
        gold.moveBefore(title);
        gold.setTrackMatte(title, TrackMatteType.ALPHA);
        title.enabled = false;

        if (variant == "A") addSheenAndStars(comp, title, gold, TY);
        else addWave(comp, title, gold);

        var rq = proj.renderQueue.items.add(comp);
        var om = rq.outputModule(1);
        try { om.applyTemplate("H.264 - Match Render Settings - 40 Mbps"); } catch (e) {}
        om.file = File(here.fullName + "/render/" + name + "_3072x1728_20s_60fps_v3");
        return comp;
    }

    // ---------- A: 부드러운 광택 + 별 반짝임 ----------
    function addSheenAndStars(comp, title, gold, TY) {
        // 넓은 솔리드 + 페더 마스크 (블러를 쓰면 솔리드 경계에서 잘려 딱딱한 띠가 됨)
        var sh = comp.layers.addSolid(WARM, "A 광택 (지나가는 빛)", 1000, 1500, 1, DUR);
        sh.blendingMode = BlendingMode.ADD;
        sh.property("Opacity").setValue(55);
        sh.property("Rotation").setValue(20);
        var mk = sh.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
        var ms = new Shape(); ms.vertices = [[420, 0], [580, 0], [580, 1500], [420, 1500]]; ms.closed = true;
        mk.property("ADBE Mask Shape").setValue(ms);
        mk.property("ADBE Mask Feather").setValue([300, 300]);
        var sp = sh.property("Position"), y = TY - 90, X0 = -500, X1 = 3600;
        // 0.8→2.6초, 10.8→12.6초에 한 번씩 지나간다. 나머지 시간은 글자 밖에서 멈춤
        var keys = [[0, X0, 1], [0.8, X0, 0], [2.6, X1, 1], [10.8, X0, 0], [12.6, X1, 1], [20, X1, 1]];
        for (var i = 0; i < keys.length; i++) sp.setValueAtTime(keys[i][0], [keys[i][1], y]);
        for (var k = 1; k <= sp.numKeys; k++)
            sp.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, keys[k - 1][2] ? KeyframeInterpolationType.HOLD : KeyframeInterpolationType.LINEAR);
        easeAll(sp);
        sh.moveBefore(gold);
        sh.setTrackMatte(title, TrackMatteType.ALPHA);

        // 별 반짝임: 글자 모서리에서 0.9초 동안 커졌다 사라짐 (10초마다 반복)
        var STARS = [[2.4, 995.5, 548], [3.3, 1766.5, 552], [6.6, 2288.5, 556], [7.4, 518.5, 691]];
        var n = 0;
        for (var rep = 0; rep < 2; rep++) for (var s = 0; s < STARS.length; s++) {
            n++;
            addStar(comp, "A 반짝임 " + n, STARS[s][0] + rep * 10, STARS[s][1] + DX, STARS[s][2]);
        }
    }
    function addStar(comp, name, t0, x, y) {
        var l = comp.layers.addShape(); l.name = name;
        var root = l.property("ADBE Root Vectors Group");
        function ell(w, h, op) {
            var g = root.addProperty("ADBE Vector Group");
            var v = g.property("ADBE Vectors Group");
            v.addProperty("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").setValue([w, h]);
            var f = v.addProperty("ADBE Vector Graphic - Fill");
            f.property("ADBE Vector Fill Color").setValue(WARM);
            f.property("ADBE Vector Fill Opacity").setValue(op);
        }
        ell(560, 7, 100); ell(7, 560, 100); ell(34, 34, 100); ell(120, 120, 30);
        var bl = l.property("Effects").addProperty("ADBE Gaussian Blur 2"); bl.property(1).setValue(4);
        l.blendingMode = BlendingMode.ADD;
        l.property("Position").setValue([x, y]);
        var sc = l.property("Scale");
        sc.setValueAtTime(t0 - 0.45, [0, 0]); sc.setValueAtTime(t0, [100, 100]); sc.setValueAtTime(t0 + 0.45, [0, 0]);
        easeAll(sc);
        var ro = l.property("Rotation");
        ro.setValueAtTime(t0 - 0.45, -15); ro.setValueAtTime(t0 + 0.45, 15);
    }

    // ---------- B: 글자 웨이브 (왼쪽부터 한 글자씩 떠오르며 밝아짐, 4초마다) ----------
    var WAVE_T = [0.8, 4.8, 8.8, 12.8, 16.8], WAVE_LEN = 1.8, WAVE_W = 30;
    function waveSelector(anim, mode) {
        var sel = anim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        sel.name = "웨이브 범위";
        sel.property("ADBE Text Percent Start").setValue(0);
        sel.property("ADBE Text Percent End").setValue(WAVE_W);
        var adv = sel.property("ADBE Text Range Advanced");
        adv.property("ADBE Text Range Type2").setValue(2);   // 공백 제외 글자 기준
        adv.property("ADBE Text Range Shape").setValue(6);   // 부드럽게
        if (mode) adv.property("ADBE Text Selector Mode").setValue(mode);
        var off = sel.property("ADBE Text Percent Offset");
        off.setValueAtTime(0, -WAVE_W);
        for (var i = 0; i < WAVE_T.length; i++) {
            off.setValueAtTime(WAVE_T[i], -WAVE_W);
            off.setValueAtTime(WAVE_T[i] + WAVE_LEN, 100);
        }
        off.setValueAtTime(DUR, 100);
        for (var k = 1; k <= off.numKeys; k++) {
            var hold = (off.keyValue(k) == 100) || off.keyTime(k) == 0;
            off.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, hold ? KeyframeInterpolationType.HOLD : KeyframeInterpolationType.LINEAR);
        }
        return sel;
    }
    function waveLift(layer) {
        var an = layer.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");
        an.name = "B 글자웨이브 (떠오름)";
        an.property("ADBE Text Animator Properties").addProperty("ADBE Text Position 3D").setValue([0, -24, 0]);
        waveSelector(an);
    }
    function addWave(comp, title, gold) {
        waveLift(title);
        // 밝아지는 부분: 같은 글자 레이어를 복제해서 웨이브 구간만 남기고 금빛을 더한다
        var hl = title.duplicate();
        hl.name = "B 웨이브 하이라이트 매트 (글자 자동연동)";
        hl.property("Source Text").expression = 'thisComp.layer("' + TITLE + '").text.sourceText';
        var an = hl.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");
        an.name = "웨이브 구간만 보이기";
        an.property("ADBE Text Animator Properties").addProperty("ADBE Text Opacity").setValue(0);
        an.property("ADBE Text Selectors").addProperty("ADBE Text Selector").name = "전체";
        waveSelector(an, 2); // 빼기: 웨이브 구간은 투명해지지 않음
        var br = comp.layers.addSolid([1, 0.9, 0.66], "B 웨이브 밝기", W, H, 1, DUR);
        br.blendingMode = BlendingMode.ADD;
        br.property("Opacity").setValue(35);
        hl.moveBefore(gold); br.moveBefore(hl);
        br.setTrackMatte(hl, TrackMatteType.ALPHA);
        hl.enabled = false;
    }

    var compA = build(NAME_A, "A");
    var compB = build(NAME_B, "B");

    app.endUndoGroup();
    Folder(here.fullName + "/render").create();
    proj.save(File(here.fullName + "/해단식_메인_3072x1728_v3.aep"));

    var log = File(here.fullName + "/render/build_log_v3.txt");
    log.open("w"); log.encoding = "UTF-8";
    log.writeln("fonts: " + GMARKET + " / " + DREAM6);
    log.writeln("comps: " + compA.name + " / " + compB.name);
    log.close();
})();

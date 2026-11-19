"""Add Simplified Chinese to the v0.5.9 runtime UI with its original settings keys."""
from pathlib import Path
import argparse
import json
import re

HERE = Path(__file__).resolve().parent
UI_PATHS = ("ui.cpp", "ui.h", "fe.cpp", "fe_sys.cpp", "ov.cpp")
FORMAT = re.compile(r"%(?:%|[-+ #0]*(?:[0-9]+|\*)?(?:\.(?:[0-9]+|\*))?(?:hh|ll|[hljztL])?[diouxXfFeEgGaAcspn])")


def load_translations():
    translations = {}
    for line in (HERE / "zh-CN.txt").read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        original, translation = line.split("|", 1)
        if original in translations:
            raise ValueError("Duplicate translation key")
        if FORMAT.findall(original) != FORMAT.findall(translation):
            raise ValueError("Format arguments changed: " + original)
        translations[original] = translation
    return translations


def edit(contents, old, new, count=1):
    actual = contents.count(old)
    if actual != count:
        raise ValueError(f"Expected {count} replacements, found {actual}: {old}")
    return contents.replace(old, new)


def prefix_parameter(contents, signature, setup):
    return edit(contents, signature, signature + "\n    " + setup)


def patch_ui(text):
    text = edit(text, "#include <algorithm>", "#include <algorithm>\n#include <string_view>\n#include <unordered_map>")
    text = edit(text, "namespace ui {", """namespace ui {

const char* tr(const char* text) {
    if (!text) return nullptr;
    static const std::unordered_map<std::string_view, const char*> translations = {
#include "zh_cn.inc"
    };
    const auto found = translations.find(text);
    return found == translations.end() ? text : found->second;
}""")
    text = edit(text, "vsnprintf(b, sizeof b, f, a)", "vsnprintf(b, sizeof b, tr(f), a)")
    anchor = "    // a symbol font for arrows and prompt glyphs, merged into the body font"
    text = edit(text, anchor, """    // Merge the Windows Simplified Chinese font into the shared dynamic atlas.
    for (const char* chinese : {"msyh.ttc", "simhei.ttf", "simsun.ttc"}) {
        const std::string path = dir + chinese;
        if (!exists(path)) continue;
        ImFontConfig config;
        config.MergeMode = true;
        config.DstFont = g_fonts.body;
        if (io.Fonts->AddFontFromFileTTF(path.c_str(), 20.0f, &config)) break;
    }
""" + anchor)
    a = text.index("    for (const char* c = s; *c; c++) {")
    b = text.index("\n}", a)
    text = text[:a] + """    for (const char* c = tr(s); *c;) {
        unsigned int codepoint;
        const int length = ImTextCharFromUtf8(&codepoint, c, nullptr);
        if (length <= 0) break;
        const char* end = c + length;
        dl->AddText(f, size, p, col, c, end);
        if (bold) dl->AddText(f, size, {p.x + size * 0.03f, p.y}, col, c, end);
        p.x += f->CalcTextSizeA(size, FLT_MAX, 0, c, end).x + spacing;
        c = end;
    }""" + text[b:]
    text = edit(text, 'ImGui::TextWrapped("%s", sub)', 'ImGui::TextWrapped("%s", tr(sub))')
    text = edit(text, 'ImGui::TextUnformatted(s)', 'ImGui::TextUnformatted(tr(s))')
    text = edit(text, 'dl->AddText({x, p.y + r - ImGui::GetFontSize() / 2}, C_TEXT, it.second);',
                'dl->AddText({x, p.y + r - ImGui::GetFontSize() / 2}, C_TEXT, tr(it.second));')
    text = edit(text, 'ImGui::CalcTextSize(it.second)', 'ImGui::CalcTextSize(tr(it.second))')
    text, changed = re.subn(
        r"(^static [^\n]*\([^\n]*const char\* label, const char\* tag,[^\n]*\) \{)",
        r"\1" + '\n    label = tr(label); tag = tr(tag);', text, flags=re.M
    )
    if changed != 1:
        raise ValueError("Could not locate the row label drawing helper")
    text, changed = re.subn(
        r"(^static [^\n]*\([^\n]*const char\* value, bool focused, float wv\) \{)",
        r"\1" + '\n    value = tr(value);', text, flags=re.M
    )
    if changed != 1:
        raise ValueError("Could not locate the choice drawing helper")
    text = edit(text, 'const char* t = *v ? "ON" : "OFF";', 'const char* t = tr(*v ? "ON" : "OFF");')
    text = edit(text, 'const char* t = value ? value : "SELECT";', 'const char* t = tr(value ? value : "SELECT");')
    text = prefix_parameter(text, 'void row_text(const char* label, const char* value, ImU32 col) {',
                            'label = tr(label); value = tr(value);')
    text = prefix_parameter(text, 'bool big_button(const char* id, const char* label, ImVec2 size, bool primary) {',
                            'label = tr(label);')
    text = prefix_parameter(text, 'void progress_bar(float frac, ImVec2 size, const char* text) {', 'text = tr(text);')
    text = prefix_parameter(text,
        'bool row_slider(const char* id, const char* label, float* v, float lo, float hi, float step, const char* text, const char* tag) {',
        'text = tr(text);')
    return text


def patch_launcher(text, dictionary):
    text = edit(text, "g_flash = s;", "g_flash = tr(s.c_str());")
    pairs = (
        ('ready ? "READY" : g.summary.c_str()', 'tr(ready ? "READY" : g.summary.c_str())'),
        ('ImGui::TextUnformatted(err.c_str())', 'ImGui::TextUnformatted(tr(err.c_str()))'),
        ('C_DIM, tiles[i].title)', 'C_DIM, tr(tiles[i].title))'),
        ('C_TEXT, tiles[i].value.c_str())', 'C_TEXT, tr(tiles[i].value.c_str()))'),
        (r'"CHANGE  \xE2\x96\xB8");', r'tr("CHANGE  \xE2\x96\xB8"));'),
        ('C_DIM, i ? "R stick" : "L stick")', 'C_DIM, tr(i ? "R stick" : "L stick"))'),
        ('C_CYAN, "HOME / GUIDE pressed")', 'C_CYAN, tr("HOME / GUIDE pressed"))'),
        ('C_DIM, PAGE_NAMES[p]);', 'C_DIM, tr(PAGE_NAMES[p]));'),
        ('C_DIM, "Game version 2.1.0")', 'C_DIM, tr("Game version 2.1.0"))'),
        ('C_DIM, "Arrows: move   Enter: select   Left / Right: change   Esc: back   F11: fullscreen")',
         'C_DIM, tr("Arrows: move   Enter: select   Left / Right: change   Esc: back   F11: fullscreen"))'),
        ('stage = g_job.stage,', 'stage = tr(g_job.stage.c_str()),'),
        (r'ImGui::Text("%s   \xC2\xB7   %d:%02d elapsed%s",', r'ImGui::Text(tr("%s   \xC2\xB7   %d:%02d elapsed%s"),'),
    )
    for old, new in pairs:
        text = edit(text, old, new)
    for phrase in (
        "Setup is still running. Stop it? (You can continue it later.)",
        "Direct3D 11 is not available: the Play screen can't open. The game will start directly.",
        "Zip archive", "Cheats", "Pipeline cache",
    ):
        text, n = re.subn(re.escape('L"' + phrase + '"'),
                          lambda _: 'L' + json.dumps(dictionary[phrase], ensure_ascii=False), text)
        if not n:
            raise ValueError("Missing wide string: " + phrase)
    text = edit(text, 'r.summary + " Anything can still be changed afterwards."',
                'r.summary + tr(" Anything can still be changed afterwards.")')
    text = edit(text, 'r.summary + (r.renderer == "vulkan_native" ? " Also: docked, shaders saved as you play, 60 FPS loading screens."\n'
                      '                                                              : " Also: docked, shaders built before playing, 60 FPS loading screens.")',
                'r.summary + tr(r.renderer == "vulkan_native" ? " Also: docked, shaders saved as you play, 60 FPS loading screens."\n'
                '                                                              : " Also: docked, shaders built before playing, 60 FPS loading screens.")')
    return text


def patch_overlay(text):
    for old, new in (
        ('C_TEXT, "MENU");', 'C_TEXT, tr("MENU"));'),
        ('0, TABS[i]);', '0, tr(TABS[i]));'),
        ('C_DIM, TABS[i]);', 'C_DIM, tr(TABS[i]));'),
        ('C_DIM, "Arrows, Enter, Left/Right, Esc to close, mouse");',
         'C_DIM, tr("Arrows, Enter, Left/Right, Esc to close, mouse"));'),
        ('C_TEXT, "Keep these display settings?");', 'C_TEXT, tr("Keep these display settings?"));'),
    ):
        text = edit(text, old, new)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    upstream = args.upstream / "runtime" / "dread_ui"
    dictionary = load_translations()
    source = {name: (upstream / name).read_text(encoding="utf-8") for name in UI_PATHS}
    out = {
        "ui.cpp": patch_ui(source["ui.cpp"]),
        "ui.h": edit(source["ui.h"], "namespace ui {", "namespace ui {\n\nconst char* tr(const char* text);"),
        "fe.cpp": patch_launcher(source["fe.cpp"], dictionary),
        "ov.cpp": patch_overlay(source["ov.cpp"]),
        "fe_sys.cpp": edit(edit(source["fe_sys.cpp"], '#include "fe.h"', '#include "fe.h"\n#include "ui.h"'), "SetTitle(wide(title)", "SetTitle(wide(ui::tr(title))", count=2),
        "zh_cn.inc": "\n".join("    {" + json.dumps(k, ensure_ascii=False) + ", "
                               + json.dumps(v, ensure_ascii=False) + "}," for k, v in dictionary.items()) + "\n",
    }
    args.output.mkdir()
    for name, text in out.items():
        with (args.output / name).open("x", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print(f"Prepared {len(out)} source files with {len(dictionary)} Simplified Chinese translations.")


if __name__ == "__main__":
    main()

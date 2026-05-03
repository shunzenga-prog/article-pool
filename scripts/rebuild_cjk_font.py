"""Rebuild DroidSansCJK with proper EM scale (2048 instead of 256).

Two-pass approach:
  Pass 1: Scale DroidSansFallbackFull glyphs and metrics by 8x, save intermediate.
  Pass 2: Replace/add ASCII glyphs from DejaVu Sans, save final font.

DroidSansFallbackFull uses units_per_EM=256, making text render 8x larger
than expected when used alongside EM=2048 fonts like DejaVu Sans.
"""
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from copy import deepcopy

SCALE = 8
INTERMEDIATE = '/tmp/DroidScaled.ttf'

def scale_font(input_path, output_path):
    """Pass 1: Scale all glyphs and metrics to EM=2048."""
    print("=== PASS 1: Scaling to EM=2048 ===")
    droid = TTFont(input_path)
    glyf = droid['glyf']

    # Scale simple glyph coordinates
    for gname in list(glyf.keys()):
        g = glyf[gname]
        if hasattr(g, 'numberOfContours') and g.numberOfContours > 0:
            scaled = [(x * SCALE, y * SCALE) for x, y in g.coordinates]
            g.coordinates = GlyphCoordinates(scaled)
            g.recalcBounds(glyf)
        elif hasattr(g, 'numberOfContours') and g.numberOfContours == -1:
            if hasattr(g, 'components'):
                for comp in g.components:
                    comp.x = int(comp.x * SCALE)
                    comp.y = int(comp.y * SCALE)

    # Scale hmtx
    for gname in list(droid['hmtx'].metrics.keys()):
        w, lsb = droid['hmtx'][gname]
        droid['hmtx'][gname] = (w * SCALE, lsb * SCALE)

    # Scale head
    droid['head'].unitsPerEm = 2048
    droid['head'].xMin *= SCALE
    droid['head'].yMin *= SCALE
    droid['head'].xMax *= SCALE
    droid['head'].yMax *= SCALE

    # Scale hhea
    hhea = droid['hhea']
    for attr in ['ascent', 'descent', 'lineGap', 'advanceWidthMax',
                 'minLeftSideBearing', 'minRightSideBearing', 'xMaxExtent']:
        setattr(hhea, attr, getattr(hhea, attr) * SCALE)

    # Scale OS/2
    os2 = droid['OS/2']
    for attr in ['sTypoAscender', 'sTypoDescender', 'sTypoLineGap',
                 'usWinAscent', 'usWinDescent', 'sxHeight', 'sCapHeight',
                 'yStrikeoutSize', 'yStrikeoutPosition',
                 'ySubscriptXSize', 'ySubscriptYSize', 'ySubscriptXOffset', 'ySubscriptYOffset',
                 'ySuperscriptXSize', 'ySuperscriptYSize', 'ySuperscriptXOffset', 'ySuperscriptYOffset']:
        if hasattr(os2, attr):
            setattr(os2, attr, getattr(os2, attr) * SCALE)

    # Scale vhea
    if 'vhea' in droid:
        for attr in ['ascent', 'descent', 'lineGap', 'advanceHeightMax',
                     'minTopSideBearing', 'minBottomSideBearing', 'yMaxExtent']:
            setattr(droid['vhea'], attr, getattr(droid['vhea'], attr) * SCALE)

    # Scale vmtx
    if 'vmtx' in droid:
        for gname in list(droid['vmtx'].metrics.keys()):
            h, tsb = droid['vmtx'][gname]
            droid['vmtx'][gname] = (h * SCALE, tsb * SCALE)

    # Scale post underline
    if 'post' in droid:
        droid['post'].underlinePosition *= SCALE
        droid['post'].underlineThickness *= SCALE

    glyf.glyphOrder = list(glyf.glyphs.keys())
    droid.save(output_path)
    print(f"  Intermediate saved to: {output_path}")


def add_ascii_glyphs(intermediate_path, dejavu_path, output_path):
    """Pass 2: Replace Droid ASCII glyphs with DejaVu Sans versions."""
    print("=== PASS 2: Adding ASCII glyphs from DejaVu Sans ===")
    dejavu = TTFont(dejavu_path)
    droid = TTFont(intermediate_path)
    dejavu_cmap = dejavu.getBestCmap()
    dejavu_glyf = dejavu['glyf']
    droid_glyf = droid['glyf']

    # Collect existing cmap
    all_entries = {}
    for table in droid['cmap'].tables:
        if hasattr(table, 'cmap'):
            for cp, gname in table.cmap.items():
                if cp not in all_entries:
                    all_entries[cp] = gname

    # Replace/add ASCII glyphs
    replaced = 0
    added = 0
    for cp in range(0x20, 0x7F):
        dejavu_gname = dejavu_cmap.get(cp)
        if dejavu_gname is None or dejavu_gname not in dejavu_glyf:
            continue

        old_gname = all_entries.get(cp)
        if old_gname and old_gname != '.notdef' and old_gname in droid_glyf.glyphs:
            # Replace existing glyph outline
            droid_glyf[old_gname] = deepcopy(dejavu_glyf[dejavu_gname])
            droid['hmtx'][old_gname] = deepcopy(dejavu['hmtx'][dejavu_gname])
            replaced += 1
        else:
            # Add new glyph
            new_name = f"uni{cp:04X}.dv"
            if new_name not in droid_glyf.glyphs:
                droid_glyf[new_name] = deepcopy(dejavu_glyf[dejavu_gname])
                droid['hmtx'][new_name] = deepcopy(dejavu['hmtx'][dejavu_gname])
                droid_glyf.glyphOrder.append(new_name)
            all_entries[cp] = new_name
            added += 1

    # Update cmap tables in-place
    for table in droid['cmap'].tables:
        if hasattr(table, 'cmap'):
            for cp in range(0x20, 0x7F):
                if cp in all_entries:
                    table.cmap[cp] = all_entries[cp]

    # Sync glyph orders
    droid_glyf.glyphOrder = list(droid_glyf.glyphs.keys())
    droid.glyphOrder = list(droid_glyf.glyphs.keys())

    # Rename font
    for record in droid['name'].names:
        if record.nameID in (1, 4, 6, 16):
            record.string = "DroidSansCJK"

    droid.save(output_path)
    print(f"  Replaced: {replaced}, Added: {added}")
    print(f"  Final font saved to: {output_path}")


if __name__ == '__main__':
    import sys
    droid_input = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
    dejavu_input = sys.argv[2] if len(sys.argv) > 2 else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    output = sys.argv[3] if len(sys.argv) > 3 else 'DroidSansCJK.ttf'

    scale_font(droid_input, INTERMEDIATE)
    add_ascii_glyphs(INTERMEDIATE, dejavu_input, output)

    # Verify
    from matplotlib.ft2font import FT2Font
    ft = FT2Font(output)
    print(f"\n=== Verification ===")
    print(f"Family: {ft.family_name}, EM: {ft.units_per_EM}")
    for ch in 'ABCabc中文字符123!@#':
        gid = ft.get_char_index(ord(ch))
        print(f"  '{ch}': gid={gid} {'OK' if gid != 0 else 'TOFU'}")
    print("Done!")

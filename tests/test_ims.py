import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from md2pdf.converter import collect_files
from md2pdf.ims import (IMS_NS, ImsItem, _rewrite_markdown_links,
                        build_ims_package, build_manifest)


ROOT = Path(__file__).resolve().parents[1]


class ImsManifestTests(unittest.TestCase):
    def test_manifest_has_organization_resources_and_order(self):
        items = [
            ImsItem(Path('/tmp/a.md'), 'a.html', 'A01: Primeiro'),
            ImsItem(Path('/tmp/b.md'), 'b.html', 'A02: Segundo'),
        ]
        xml = build_manifest(items, 'UD1')
        root = ET.fromstring(xml)
        ns = {'i': IMS_NS}

        self.assertEqual(root.tag, f'{{{IMS_NS}}}manifest')
        self.assertEqual(root.findtext('i:metadata/i:schemaversion', namespaces=ns),
                         '1.1.4')
        orgs = root.find('i:organizations', ns)
        self.assertIsNotNone(orgs)
        org = orgs.find('i:organization', ns)
        self.assertEqual(org.findtext('i:title', namespaces=ns), 'UD1')
        self.assertEqual(
            [node.findtext('i:title', namespaces=ns)
             for node in org.findall('i:item', ns)],
            ['A01: Primeiro', 'A02: Segundo'],
        )
        resources = root.findall('i:resources/i:resource', ns)
        self.assertEqual([r.get('href') for r in resources], ['a.html', 'b.html'])
        self.assertTrue(all(r.get('type') == 'webcontent' for r in resources))


class ImsPackageTests(unittest.TestCase):
    @unittest.skipUnless((ROOT / 'md2pdf.html').exists(), 'template HTML non dispoñible')
    def test_package_contains_manifest_html_and_rewrites_md_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            a = d / 'U1A1_Primeiro.md'
            b = d / 'U1A2_Segundo.md'
            a.write_text('''---\nactivity: "A01: Primeiro"\n---\n\n# Primeiro\n\n[Vai ao segundo](U1A2_Segundo.md#detalle)\n''', encoding='utf-8')
            b.write_text('''---\nactivity: "A02: Segundo"\n---\n\n# Segundo\n\n## Detalle {#detalle}\n\nContido.\n''', encoding='utf-8')
            out = d / 'ud1.zip'

            ok = build_ims_package(
                [a, b], out, ROOT / 'md2pdf.html', package_title='UD1',
                highlight=str(ROOT / 'drake-jb.theme'), strict=True,
            )
            self.assertTrue(ok)
            self.assertTrue(out.exists())

            with zipfile.ZipFile(out) as archive:
                names = archive.namelist()
                self.assertEqual(names[0], 'imsmanifest.xml')
                self.assertIn('U1A1_Primeiro.html', names)
                self.assertIn('U1A2_Segundo.html', names)
                html = archive.read('U1A1_Primeiro.html').decode('utf-8')
                self.assertIn('href="U1A2_Segundo.html#detalle"', html)
                self.assertNotIn('href="U1A2_Segundo.md#detalle"', html)

                manifest = ET.fromstring(archive.read('imsmanifest.xml'))
                ns = {'i': IMS_NS}
                titles = [
                    node.findtext('i:title', namespaces=ns)
                    for node in manifest.findall('i:organizations/i:organization/i:item', ns)
                ]
                self.assertEqual(titles, ['A01: Primeiro', 'A02: Segundo'])

    def test_strict_rejects_markdown_link_outside_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            a = d / 'a.md'
            a.write_text('# A\n\n[Fóra](non-incluido.md)\n', encoding='utf-8')
            out = d / 'bad.zip'

            ok = build_ims_package(
                [a], out, ROOT / 'md2pdf.html',
                highlight=str(ROOT / 'drake-jb.theme'), strict=True,
            )
            self.assertFalse(ok)
            self.assertFalse(out.exists())


class ImsResourceTests(unittest.TestCase):
    def test_directory_order_is_natural(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            for name in ('U1A10.md', 'U1A2.md', 'U1A1.md'):
                (d / name).write_text('# x\n', encoding='utf-8')
            self.assertEqual([p.name for p in collect_files([str(d)])],
                             ['U1A1.md', 'U1A2.md', 'U1A10.md'])

    def test_local_files_are_packaged_and_missing_ones_warned(self):
        with tempfile.TemporaryDirectory() as temporary:
            d = Path(temporary)
            (d / 'recursos').mkdir()
            (d / 'recursos' / 'partida.zip').write_bytes(b'PK')
            source = d / 'a.md'
            html = ('<a href="recursos/partida.zip">zip</a> '
                    '<a href="falta.pdf">pdf</a> <a href="https://x.org/a.pdf">web</a>')
            assets: dict[Path, str] = {}
            used: set[str] = set()
            out, warnings = _rewrite_markdown_links(html, source, {}, assets, used)
            self.assertIn('href="recursos/partida.zip"', out)
            self.assertEqual(used, {'recursos/partida.zip'})
            self.assertEqual(list(assets.values()), ['recursos/partida.zip'])
            self.assertIn('href="https://x.org/a.pdf"', out)
            self.assertEqual(len(warnings), 1)
            self.assertIn('falta.pdf', warnings[0])

    def test_manifest_lists_resource_files(self):
        items = [ImsItem(Path('/tmp/a.md'), 'a.html', 'A', ('recursos/partida.zip',))]
        root = ET.fromstring(build_manifest(items, 'UD1'))
        ns = {'i': IMS_NS}
        files = [f.get('href') for f in root.findall('i:resources/i:resource/i:file', ns)]
        self.assertEqual(files, ['a.html', 'recursos/partida.zip'])


if __name__ == '__main__':
    unittest.main()

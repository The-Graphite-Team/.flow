import unittest
import xml.etree.ElementTree as ET

from flow_runner import FlowSyntaxError, SVG_NS, parse_flowchart, render_flowchart


class ParseTests(unittest.TestCase):
    def test_inline_chain_positions_and_connectors(self):
        diagram = parse_flowchart("Start -> Check -> Finish")
        self.assertEqual([n.label for n in diagram.nodes], ["Start", "Check", "Finish"])
        self.assertEqual(len(diagram.arrows), 2)
        self.assertEqual(diagram.nodes[1].x, diagram.nodes[0].x + 264)

    def test_new_main_line_starts_next_row(self):
        diagram = parse_flowchart("Start\nNext")
        self.assertEqual(diagram.nodes[1].x, diagram.nodes[0].x)
        self.assertGreater(diagram.nodes[1].y, diagram.nodes[0].y)
        self.assertEqual(len(diagram.arrows), 1)

    def test_indented_line_continues_branch(self):
        diagram = parse_flowchart("Start\n    Branch A -> Branch B")
        self.assertEqual([n.label for n in diagram.nodes], ["Start", "Branch A", "Branch B"])
        self.assertEqual(diagram.nodes[1].y, diagram.nodes[0].y)
        self.assertEqual(len(diagram.arrows), 2)

    def test_warning_marker(self):
        diagram = parse_flowchart("Overheat!")
        self.assertTrue(diagram.nodes[0].warning)
        self.assertEqual(diagram.nodes[0].label, "Overheat")

    def test_comments_and_blank_lines(self):
        diagram = parse_flowchart("# heading\n\nStart\n  # branch comment\n  Next")
        self.assertEqual([n.label for n in diagram.nodes], ["Start", "Next"])

    def test_typed_nodes_and_decision_branches(self):
        diagram = parse_flowchart(
            "start: Boot\ndecision: Safe?\n  yes: Continue\n  no: warning: Stop!"
        )
        self.assertEqual([n.kind for n in diagram.nodes], ["start", "decision", "process", "warning"])
        self.assertEqual(diagram.nodes[2].branch, "YES")
        self.assertEqual(diagram.nodes[3].branch, "NO")
        self.assertTrue(diagram.nodes[3].warning)

    def test_typed_node_shapes_render(self):
        document = render_flowchart(
            "start: Boot\ndecision: Ready?\n  yes: end: Done"
        )
        self.assertIn("<polygon", document)
        self.assertIn("#dcfce7", document)
        self.assertIn("YES", document)

    def test_legacy_untyped_syntax_still_works(self):
        diagram = parse_flowchart("Start -> Check -> Finish")
        self.assertEqual([n.kind for n in diagram.nodes], ["process", "process", "process"])

    def test_rejects_orphan_indentation(self):
        with self.assertRaisesRegex(FlowSyntaxError, "preceding node"):
            parse_flowchart("  Orphan")

    def test_rejects_empty_arrow_segments(self):
        for source in ("A ->", "-> B", "A -> -> B"):
            with self.subTest(source=source), self.assertRaises(FlowSyntaxError):
                parse_flowchart(source)

    def test_rejects_empty_document(self):
        with self.assertRaises(FlowSyntaxError):
            parse_flowchart("# only a comment\n\n")


class RenderTests(unittest.TestCase):
    def test_svg_is_well_formed_and_uses_correct_namespace(self):
        document = render_flowchart("Start -> Finish", "Demo")
        start = document.index("<svg")
        end = document.index("</svg>") + len("</svg>")
        root = ET.fromstring(document[start:end])
        self.assertEqual(root.tag, f"{{{SVG_NS}}}svg")
        self.assertEqual(len(root.findall(f".//{{{SVG_NS}}}rect")), 2)

    def test_labels_and_title_are_escaped(self):
        document = render_flowchart("<script>alert('x')</script>", "A < B")
        self.assertNotIn("<script>alert", document)
        self.assertIn("&lt;script&gt;", document)
        self.assertIn("A &lt; B", document)


if __name__ == "__main__":
    unittest.main()

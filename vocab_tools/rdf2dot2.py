"""
RDF2DOT2 is a modified version of rdflib.tools.rdf2dot.

The principle changes are for nod color adjustment.

---
A commandline tool for drawing RDF graphs in Graphviz DOT format

You can draw the graph of an RDF file directly:

.. code-block: bash

   rdf2dot my_rdf_file.rdf | dot -Tpng | display

"""

import collections
import html
import sys

import rdflib
import rdflib.extras.cmdlineutils
from rdflib import XSD

LABEL_PROPERTIES = [
    rdflib.RDFS.label,
    rdflib.URIRef("http://purl.org/dc/elements/1.1/title"),
    rdflib.URIRef("http://xmlns.com/foaf/0.1/name"),
    rdflib.URIRef("http://www.w3.org/2006/vcard/ns#fn"),
    rdflib.URIRef("http://www.w3.org/2006/vcard/ns#org"),
]

XSDTERMS = [
    XSD[x]
    for x in (
        "anyURI",
        "base64Binary",
        "boolean",
        "byte",
        "date",
        "dateTime",
        "decimal",
        "double",
        "duration",
        "float",
        "gDay",
        "gMonth",
        "gMonthDay",
        "gYear",
        "gYearMonth",
        "hexBinary",
        "ID",
        "IDREF",
        "IDREFS",
        "int",
        "integer",
        "language",
        "long",
        "Name",
        "NCName",
        "negativeInteger",
        "NMTOKEN",
        "NMTOKENS",
        "nonNegativeInteger",
        "nonPositiveInteger",
        "normalizedString",
        "positiveInteger",
        "QName",
        "short",
        "string",
        "time",
        "token",
        "unsignedByte",
        "unsignedInt",
        "unsignedLong",
        "unsignedShort",
    )
]

class Settings(dict):

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError()


DEFAULTS = Settings({
    "FONTNAME" : "Helvetica",
    "FONTSIZE" : "11",
    "FFONTNAME" : "Cousine",
    "FFONTSIZE" : "11",
    "RELCOLOR" : "black", ##336633
    "RELFONTNAME" : "Cousine",
    "EDGECOLOR" : "blue",
    "NODECOLOR" : "black",
    "ISACOLOR" : "black",
    "TABLECOLOR" : "black",
    "TDBGCOLOR1" : "#dddddd",
    "TDBGCOLOR2" : "#eeeeee",
    "HREFCOLOR" : "#6666ff"
})


def rdf2dot(g, stream, options={}):
    """
    Convert the RDF graph to DOT
    writes the dot output to the stream
    """

    fields = collections.defaultdict(set)
    nodes = {}
    opts = Settings(DEFAULTS)
    opts.update(options)

    def node(x):
        if x not in nodes:
            nodes[x] = "node%d" % len(nodes)
        return nodes[x]

    def label(x, g):
        for labelProp in LABEL_PROPERTIES:
            l_ = g.value(x, labelProp)
            if l_:
                return l_
        try:
            return g.namespace_manager.compute_qname(x)[2]
        except Exception:
            return x

    def formatliteral(l, g):
        v = html.escape(l)
        if l.datatype:
            return "&quot;%s&quot;^^%s" % (v, qname(l.datatype, g))
        elif l.language:
            return "&quot;%s&quot;@%s" % (v, l.language)
        return "&quot;%s&quot;" % v

    def qname(x, g):
        try:
            q = g.compute_qname(x)
            return q[0] + ":" + q[2]
        except Exception:
            return x

    def color(p):
        return "BLACK"

    stream.write('digraph { \n node [ fontname="%s" fontsize="%s"] ; \n' % (opts.FONTNAME, opts.FONTSIZE))

    for s, p, o, d in g:
        sn = node(s)
        if p == rdflib.RDFS.label:
            continue
        if isinstance(o, (rdflib.URIRef, rdflib.BNode)):
            on = node(o)
            opstr = (
                f"\t%s -> %s [ color=%s, label=< <font point-size='{opts.FONTSIZE}' "
                + f"color='{opts.RELCOLOR}' face='{opts.RELFONTNAME}'>%s</font> > ] ;\n"
            )
            stream.write(opstr % (sn, on, color(p), qname(p, g)))
        else:
            fields[sn].add((qname(p, g), formatliteral(o, g)))

    for u, n in nodes.items():
        stream.write("# %s %s\n" % (u, n))
        f = [
            f"<tr><td align='left'><FONT FACE='{opts.FFONTNAME}' POINT-SIZE='{opts.FFONTSIZE}'>%s</FONT></td><td align='left'>%s</td></tr>" % x
            for x in sorted(fields[n])
        ]
        opstr = (
            f"%s [ shape=none, color=%s label=< <table color='{opts.TABLECOLOR}'"
            + " cellborder='0' cellspacing='1' border='1'><tr>"
            + f"<td colspan='2' bgcolor='{opts.TDBGCOLOR1}'><B>%s</B></td></tr><tr>"
            + f"<td href='%s' bgcolor='{opts.TDBGCOLOR2}' cellspacing='0' colspan='2'>"
            + f"<font point-size='{opts.FONTSIZE}' color='{opts.HREFCOLOR}'>%s</font></td>"
            + "</tr>%s</table> > ] \n"
        )
        stream.write(
            opstr
            % (n, opts.NODECOLOR, html.escape(label(u, g)), u, html.escape(u), "".join(f))
        )

    stream.write("}\n")



def _help():
    sys.stderr.write(
        """
rdf2dot.py [-f <format>] files...
Read RDF files given on STDOUT, writes a graph of the RDFS schema in DOT
language to stdout
-f specifies parser to use, if not given,

"""
    )


def main():
    rdflib.extras.cmdlineutils.main(rdf2dot, _help)



if __name__ == "__main__":
    main()
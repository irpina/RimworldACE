"""Minimal ECMA-335 CLI metadata + IL reader.

Enough to locate a type, list its methods, and disassemble their IL bodies.
Written because no decompiler is installed on this machine; pefile is.
Not general-purpose - it implements the tables we actually need to read
RimWorld's market value calculation.
"""
import struct
import pefile

# ---------------------------------------------------------------- tables

TABLE_NAMES = {
    0: "Module", 1: "TypeRef", 2: "TypeDef", 4: "Field", 6: "MethodDef",
    8: "Param", 9: "InterfaceImpl", 10: "MemberRef", 11: "Constant",
    12: "CustomAttribute", 13: "FieldMarshal", 14: "DeclSecurity",
    15: "ClassLayout", 16: "FieldLayout", 17: "StandAloneSig",
    18: "EventMap", 20: "Event", 21: "PropertyMap", 23: "Property",
    24: "MethodSemantics", 25: "MethodImpl", 26: "ModuleRef",
    27: "TypeSpec", 28: "ImplMap", 29: "FieldRVA", 32: "Assembly",
    33: "AssemblyProcessor", 34: "AssemblyOS", 35: "AssemblyRef",
    36: "AssemblyRefProcessor", 37: "AssemblyRefOS", 38: "File",
    39: "ExportedType", 40: "ManifestResource", 41: "NestedClass",
    42: "GenericParam", 43: "MethodSpec", 44: "GenericParamConstraint",
}

# Coded index definitions: name -> (list of table ids, tag bit count)
CODED = {
    "TypeDefOrRef": ([2, 1, 27], 2),
    "HasConstant": ([4, 8, 23], 2),
    "HasCustomAttribute": ([6, 4, 1, 2, 8, 9, 10, 0, 14, 27, 32, 35, 38,
                            39, 40, 26, 20, 23, 17, 42, 43, 44], 5),
    "HasFieldMarshal": ([4, 8], 1),
    "HasDeclSecurity": ([2, 6, 32], 2),
    "MemberRefParent": ([2, 1, 26, 6, 27], 3),
    "HasSemantics": ([20, 23], 1),
    "MethodDefOrRef": ([6, 10], 1),
    "MemberForwarded": ([4, 6], 1),
    "Implementation": ([38, 39, 40], 2),
    "CustomAttributeType": ([-1, -1, 6, 10, -1], 3),
    "ResolutionScope": ([0, 26, 35, 1], 2),
    "TypeOrMethodDef": ([2, 6], 1),
}

# Column layouts. 'S'=#Strings, 'G'=#GUID, 'B'=#Blob, '2'=uint16, '4'=uint32,
# '~<table>'=simple index into table, coded index by name.
SCHEMA = {
    0:  [("Generation", "2"), ("Name", "S"), ("Mvid", "G"),
         ("EncId", "G"), ("EncBaseId", "G")],
    1:  [("ResolutionScope", "ResolutionScope"), ("Name", "S"),
         ("Namespace", "S")],
    2:  [("Flags", "4"), ("Name", "S"), ("Namespace", "S"),
         ("Extends", "TypeDefOrRef"), ("FieldList", "~4"),
         ("MethodList", "~6")],
    4:  [("Flags", "2"), ("Name", "S"), ("Signature", "B")],
    6:  [("RVA", "4"), ("ImplFlags", "2"), ("Flags", "2"), ("Name", "S"),
         ("Signature", "B"), ("ParamList", "~8")],
    8:  [("Flags", "2"), ("Sequence", "2"), ("Name", "S")],
    9:  [("Class", "~2"), ("Interface", "TypeDefOrRef")],
    10: [("Class", "MemberRefParent"), ("Name", "S"), ("Signature", "B")],
    11: [("Type", "2"), ("Parent", "HasConstant"), ("Value", "B")],
    12: [("Parent", "HasCustomAttribute"), ("Type", "CustomAttributeType"),
         ("Value", "B")],
    13: [("Parent", "HasFieldMarshal"), ("NativeType", "B")],
    14: [("Action", "2"), ("Parent", "HasDeclSecurity"),
         ("PermissionSet", "B")],
    15: [("PackingSize", "2"), ("ClassSize", "4"), ("Parent", "~2")],
    16: [("Offset", "4"), ("Field", "~4")],
    17: [("Signature", "B")],
    18: [("Parent", "~2"), ("EventList", "~20")],
    20: [("EventFlags", "2"), ("Name", "S"), ("EventType", "TypeDefOrRef")],
    21: [("Parent", "~2"), ("PropertyList", "~23")],
    23: [("Flags", "2"), ("Name", "S"), ("Type", "B")],
    24: [("Semantics", "2"), ("Method", "~6"), ("Association", "HasSemantics")],
    25: [("Class", "~2"), ("MethodBody", "MethodDefOrRef"),
         ("MethodDeclaration", "MethodDefOrRef")],
    26: [("Name", "S")],
    27: [("Signature", "B")],
    28: [("MappingFlags", "2"), ("MemberForwarded", "MemberForwarded"),
         ("ImportName", "S"), ("ImportScope", "~26")],
    29: [("RVA", "4"), ("Field", "~4")],
    32: [("HashAlgId", "4"), ("Major", "2"), ("Minor", "2"), ("Build", "2"),
         ("Rev", "2"), ("Flags", "4"), ("PublicKey", "B"), ("Name", "S"),
         ("Culture", "S")],
    33: [("Processor", "4")],
    34: [("OSPlatformID", "4"), ("OSMajor", "4"), ("OSMinor", "4")],
    35: [("Major", "2"), ("Minor", "2"), ("Build", "2"), ("Rev", "2"),
         ("Flags", "4"), ("PublicKeyOrToken", "B"), ("Name", "S"),
         ("Culture", "S"), ("HashValue", "B")],
    36: [("Processor", "4"), ("AssemblyRef", "~35")],
    37: [("OSPlatformID", "4"), ("OSMajor", "4"), ("OSMinor", "4"),
         ("AssemblyRef", "~35")],
    38: [("Flags", "4"), ("Name", "S"), ("HashValue", "B")],
    39: [("Flags", "4"), ("TypeDefId", "4"), ("Name", "S"),
         ("Namespace", "S"), ("Implementation", "Implementation")],
    40: [("Offset", "4"), ("Flags", "4"), ("Name", "S"),
         ("Implementation", "Implementation")],
    41: [("NestedClass", "~2"), ("EnclosingClass", "~2")],
    42: [("Number", "2"), ("Flags", "2"), ("Owner", "TypeOrMethodDef"),
         ("Name", "S")],
    43: [("Method", "MethodDefOrRef"), ("Instantiation", "B")],
    44: [("Owner", "~42"), ("Constraint", "TypeDefOrRef")],
}


class Assembly:
    def __init__(self, path):
        self.pe = pefile.PE(path, fast_load=True)
        # pefile may hand back an mmap; we want real bytes for .index()
        self.data = bytes(self.pe.__data__)
        self._load_metadata()

    # -- RVA mapping ----------------------------------------------------
    def rva_to_off(self, rva):
        for s in self.pe.sections:
            start = s.VirtualAddress
            size = max(s.Misc_VirtualSize, s.SizeOfRawData)
            if start <= rva < start + size:
                return s.PointerToRawData + (rva - start)
        raise ValueError(f"RVA {rva:#x} not in any section")

    # -- metadata root --------------------------------------------------
    def _load_metadata(self):
        cli_rva = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[14].VirtualAddress
        o = self.rva_to_off(cli_rva)
        md_rva, md_size = struct.unpack_from("<II", self.data, o + 8)
        m = self.rva_to_off(md_rva)
        self.md_base = m

        sig, = struct.unpack_from("<I", self.data, m)
        assert sig == 0x424A5342, "bad metadata signature"
        vlen, = struct.unpack_from("<I", self.data, m + 12)
        p = m + 16 + vlen
        p += 2  # flags
        nstreams, = struct.unpack_from("<H", self.data, p)
        p += 2

        self.streams = {}
        for _ in range(nstreams):
            off, size = struct.unpack_from("<II", self.data, p)
            p += 8
            end = self.data.index(b"\0", p)
            name = self.data[p:end].decode("ascii")
            p = end + 1
            p = (p + 3) & ~3  # 4-byte align
            self.streams[name] = (m + off, size)

        self._parse_tables()

    # -- heaps ----------------------------------------------------------
    def string(self, idx):
        base, size = self.streams["#Strings"]
        end = self.data.index(b"\0", base + idx)
        return self.data[base + idx:end].decode("utf-8", "replace")

    def blob(self, idx):
        base, _ = self.streams["#Blob"]
        p = base + idx
        b0 = self.data[p]
        if b0 & 0x80 == 0:
            ln, p = b0 & 0x7F, p + 1
        elif b0 & 0xC0 == 0x80:
            ln = ((b0 & 0x3F) << 8) | self.data[p + 1]
            p += 2
        else:
            ln = (((b0 & 0x1F) << 24) | (self.data[p + 1] << 16) |
                  (self.data[p + 2] << 8) | self.data[p + 3])
            p += 4
        return self.data[p:p + ln]

    def userstring(self, idx):
        base, _ = self.streams["#US"]
        p = base + idx
        b0 = self.data[p]
        if b0 & 0x80 == 0:
            ln, p = b0 & 0x7F, p + 1
        elif b0 & 0xC0 == 0x80:
            ln = ((b0 & 0x3F) << 8) | self.data[p + 1]
            p += 2
        else:
            ln = (((b0 & 0x1F) << 24) | (self.data[p + 1] << 16) |
                  (self.data[p + 2] << 8) | self.data[p + 3])
            p += 4
        raw = self.data[p:p + ln]
        if ln and ln % 2 == 1:
            raw = raw[:-1]  # trailing terminal byte
        return raw.decode("utf-16-le", "replace")

    # -- tables ---------------------------------------------------------
    def _parse_tables(self):
        base, _ = self.streams["#~"]
        heap_sizes = self.data[base + 6]
        self.s_wide = bool(heap_sizes & 1)
        self.g_wide = bool(heap_sizes & 2)
        self.b_wide = bool(heap_sizes & 4)
        valid, sorted_ = struct.unpack_from("<QQ", self.data, base + 8)

        p = base + 24
        self.rows = {}
        for t in range(64):
            if valid >> t & 1:
                self.rows[t], = struct.unpack_from("<I", self.data, p)
                p += 4

        # column widths depend on row counts, so size everything first
        self._col_size = {}
        self._row_size = {}
        for t in self.rows:
            sizes = [self._width(c[1]) for c in SCHEMA[t]]
            self._col_size[t] = sizes
            self._row_size[t] = sum(sizes)

        self.table_off = {}
        for t in sorted(self.rows):
            self.table_off[t] = p
            p += self._row_size[t] * self.rows[t]

    def _width(self, kind):
        if kind == "2":
            return 2
        if kind == "4":
            return 4
        if kind == "S":
            return 4 if self.s_wide else 2
        if kind == "G":
            return 4 if self.g_wide else 2
        if kind == "B":
            return 4 if self.b_wide else 2
        if kind.startswith("~"):
            t = int(kind[1:])
            return 4 if self.rows.get(t, 0) >= (1 << 16) else 2
        tables, bits = CODED[kind]
        mx = 0
        for tt in tables:
            if tt >= 0:
                mx = max(mx, self.rows.get(tt, 0))
        return 4 if mx >= (1 << (16 - bits)) else 2

    def row(self, table, index):
        """1-based row index, per ECMA-335."""
        if index < 1 or index > self.rows.get(table, 0):
            return None
        off = self.table_off[table] + (index - 1) * self._row_size[table]
        out = {}
        for (name, kind), w in zip(SCHEMA[table], self._col_size[table]):
            v = (struct.unpack_from("<H", self.data, off)[0] if w == 2
                 else struct.unpack_from("<I", self.data, off)[0])
            off += w
            if kind in CODED:
                tables, bits = CODED[kind]
                tag = v & ((1 << bits) - 1)
                ri = v >> bits
                tt = tables[tag] if tag < len(tables) else -1
                out[name] = (tt, ri)
            else:
                out[name] = v
        return out

    def iter_table(self, table):
        for i in range(1, self.rows.get(table, 0) + 1):
            yield i, self.row(table, i)

    # -- convenience ----------------------------------------------------
    def find_type(self, name, namespace=None):
        for i, r in self.iter_table(2):
            if self.string(r["Name"]) == name:
                if namespace is None or self.string(r["Namespace"]) == namespace:
                    return i, r
        return None, None

    def type_methods(self, typedef_index):
        r = self.row(2, typedef_index)
        start = r["MethodList"]
        nxt = self.row(2, typedef_index + 1)
        end = nxt["MethodList"] if nxt else self.rows[6] + 1
        out = []
        for mi in range(start, end):
            mr = self.row(6, mi)
            if mr:
                out.append((mi, self.string(mr["Name"]), mr))
        return out

    def type_fullname_by_token(self, tt, ri):
        if tt == 2:
            r = self.row(2, ri)
            if not r:
                return "?"
            ns = self.string(r["Namespace"])
            n = self.string(r["Name"])
            return f"{ns}.{n}" if ns else n
        if tt == 1:
            r = self.row(1, ri)
            if not r:
                return "?"
            ns = self.string(r["Namespace"])
            n = self.string(r["Name"])
            return f"{ns}.{n}" if ns else n
        if tt == 27:
            return "TypeSpec"
        return "?"

    # -- method bodies --------------------------------------------------
    def method_il(self, method_row):
        rva = method_row["RVA"]
        if rva == 0:
            return None, None
        o = self.rva_to_off(rva)
        b0 = self.data[o]
        if (b0 & 3) == 2:  # tiny
            size = b0 >> 2
            return self.data[o + 1:o + 1 + size], None
        # fat
        flags_size, = struct.unpack_from("<H", self.data, o)
        hsize = (flags_size >> 12) * 4
        code_size, = struct.unpack_from("<I", self.data, o + 4)
        local_tok, = struct.unpack_from("<I", self.data, o + 8)
        return self.data[o + hsize:o + hsize + code_size], local_tok

    # -- token resolution ------------------------------------------------
    def resolve_token(self, tok):
        table = tok >> 24
        ri = tok & 0xFFFFFF
        if table == 0x0A:  # MemberRef
            r = self.row(10, ri)
            if not r:
                return f"memberref#{ri}"
            parent = self.type_fullname_by_token(*r["Class"])
            return f"{parent}::{self.string(r['Name'])}"
        if table == 0x06:  # MethodDef
            r = self.row(6, ri)
            if not r:
                return f"method#{ri}"
            return f"{self._owner_of_method(ri)}::{self.string(r['Name'])}"
        if table == 0x04:  # Field
            r = self.row(4, ri)
            if not r:
                return f"field#{ri}"
            return f"{self._owner_of_field(ri)}::{self.string(r['Name'])}"
        if table == 0x01:
            return self.type_fullname_by_token(1, ri)
        if table == 0x02:
            return self.type_fullname_by_token(2, ri)
        if table == 0x1B:
            return "TypeSpec"
        if table == 0x2B:  # MethodSpec
            r = self.row(43, ri)
            if r:
                tt, rri = r["Method"]
                return self.resolve_token(((0x06 if tt == 6 else 0x0A) << 24) | rri)
        if table == 0x70:  # UserString
            return repr(self.userstring(ri))
        return f"tok{tok:#x}"

    def _build_owner_maps(self):
        if hasattr(self, "_mowner"):
            return
        self._mowner = {}
        self._fowner = {}
        n = self.rows.get(2, 0)
        for i in range(1, n + 1):
            r = self.row(2, i)
            nxt = self.row(2, i + 1)
            ns = self.string(r["Namespace"])
            nm = self.string(r["Name"])
            full = f"{ns}.{nm}" if ns else nm
            ms = r["MethodList"]
            me = nxt["MethodList"] if nxt else self.rows.get(6, 0) + 1
            for k in range(ms, me):
                self._mowner[k] = full
            fs = r["FieldList"]
            fe = nxt["FieldList"] if nxt else self.rows.get(4, 0) + 1
            for k in range(fs, fe):
                self._fowner[k] = full

    def _owner_of_method(self, mi):
        self._build_owner_maps()
        return self._mowner.get(mi, "?")

    def _owner_of_field(self, fi):
        self._build_owner_maps()
        return self._fowner.get(fi, "?")


# ---------------------------------------------------------------- IL

# opcode -> (name, operand kind)
# operand kinds: none, i1, u1, i4, i8, r4, r8, tok, str, br1, br4, switch, var1, var2
OPS = {
    0x00: ("nop", "none"), 0x01: ("break", "none"),
    0x02: ("ldarg.0", "none"), 0x03: ("ldarg.1", "none"),
    0x04: ("ldarg.2", "none"), 0x05: ("ldarg.3", "none"),
    0x06: ("ldloc.0", "none"), 0x07: ("ldloc.1", "none"),
    0x08: ("ldloc.2", "none"), 0x09: ("ldloc.3", "none"),
    0x0A: ("stloc.0", "none"), 0x0B: ("stloc.1", "none"),
    0x0C: ("stloc.2", "none"), 0x0D: ("stloc.3", "none"),
    0x0E: ("ldarg.s", "u1"), 0x0F: ("ldarga.s", "u1"),
    0x10: ("starg.s", "u1"), 0x11: ("ldloc.s", "u1"),
    0x12: ("ldloca.s", "u1"), 0x13: ("stloc.s", "u1"),
    0x14: ("ldnull", "none"), 0x15: ("ldc.i4.m1", "none"),
    0x16: ("ldc.i4.0", "none"), 0x17: ("ldc.i4.1", "none"),
    0x18: ("ldc.i4.2", "none"), 0x19: ("ldc.i4.3", "none"),
    0x1A: ("ldc.i4.4", "none"), 0x1B: ("ldc.i4.5", "none"),
    0x1C: ("ldc.i4.6", "none"), 0x1D: ("ldc.i4.7", "none"),
    0x1E: ("ldc.i4.8", "none"), 0x1F: ("ldc.i4.s", "i1"),
    0x20: ("ldc.i4", "i4"), 0x21: ("ldc.i8", "i8"),
    0x22: ("ldc.r4", "r4"), 0x23: ("ldc.r8", "r8"),
    0x25: ("dup", "none"), 0x26: ("pop", "none"),
    0x27: ("jmp", "tok"), 0x28: ("call", "tok"),
    0x29: ("calli", "tok"), 0x2A: ("ret", "none"),
    0x2B: ("br.s", "br1"), 0x2C: ("brfalse.s", "br1"),
    0x2D: ("brtrue.s", "br1"), 0x2E: ("beq.s", "br1"),
    0x2F: ("bge.s", "br1"), 0x30: ("bgt.s", "br1"),
    0x31: ("ble.s", "br1"), 0x32: ("blt.s", "br1"),
    0x33: ("bne.un.s", "br1"), 0x34: ("bge.un.s", "br1"),
    0x35: ("bgt.un.s", "br1"), 0x36: ("ble.un.s", "br1"),
    0x37: ("blt.un.s", "br1"), 0x38: ("br", "br4"),
    0x39: ("brfalse", "br4"), 0x3A: ("brtrue", "br4"),
    0x3B: ("beq", "br4"), 0x3C: ("bge", "br4"),
    0x3D: ("bgt", "br4"), 0x3E: ("ble", "br4"),
    0x3F: ("blt", "br4"), 0x40: ("bne.un", "br4"),
    0x41: ("bge.un", "br4"), 0x42: ("bgt.un", "br4"),
    0x43: ("ble.un", "br4"), 0x44: ("blt.un", "br4"),
    0x45: ("switch", "switch"),
    0x46: ("ldind.i1", "none"), 0x47: ("ldind.u1", "none"),
    0x48: ("ldind.i2", "none"), 0x49: ("ldind.u2", "none"),
    0x4A: ("ldind.i4", "none"), 0x4B: ("ldind.u4", "none"),
    0x4C: ("ldind.i8", "none"), 0x4D: ("ldind.i", "none"),
    0x4E: ("ldind.r4", "none"), 0x4F: ("ldind.r8", "none"),
    0x50: ("ldind.ref", "none"), 0x51: ("stind.ref", "none"),
    0x52: ("stind.i1", "none"), 0x53: ("stind.i2", "none"),
    0x54: ("stind.i4", "none"), 0x55: ("stind.i8", "none"),
    0x56: ("stind.r4", "none"), 0x57: ("stind.r8", "none"),
    0x58: ("add", "none"), 0x59: ("sub", "none"),
    0x5A: ("mul", "none"), 0x5B: ("div", "none"),
    0x5C: ("div.un", "none"), 0x5D: ("rem", "none"),
    0x5E: ("rem.un", "none"), 0x5F: ("and", "none"),
    0x60: ("or", "none"), 0x61: ("xor", "none"),
    0x62: ("shl", "none"), 0x63: ("shr", "none"),
    0x64: ("shr.un", "none"), 0x65: ("neg", "none"),
    0x66: ("not", "none"),
    0x67: ("conv.i1", "none"), 0x68: ("conv.i2", "none"),
    0x69: ("conv.i4", "none"), 0x6A: ("conv.i8", "none"),
    0x6B: ("conv.r4", "none"), 0x6C: ("conv.r8", "none"),
    0x6D: ("conv.u4", "none"), 0x6E: ("conv.u8", "none"),
    0x6F: ("callvirt", "tok"), 0x70: ("cpobj", "tok"),
    0x71: ("ldobj", "tok"), 0x72: ("ldstr", "str"),
    0x73: ("newobj", "tok"), 0x74: ("castclass", "tok"),
    0x75: ("isinst", "tok"), 0x76: ("conv.r.un", "none"),
    0x79: ("unbox", "tok"), 0x7A: ("throw", "none"),
    0x7B: ("ldfld", "tok"), 0x7C: ("ldflda", "tok"),
    0x7D: ("stfld", "tok"), 0x7E: ("ldsfld", "tok"),
    0x7F: ("ldsflda", "tok"), 0x80: ("stsfld", "tok"),
    0x81: ("stobj", "tok"),
    0x82: ("conv.ovf.i1.un", "none"), 0x83: ("conv.ovf.i2.un", "none"),
    0x84: ("conv.ovf.i4.un", "none"), 0x85: ("conv.ovf.i8.un", "none"),
    0x86: ("conv.ovf.u1.un", "none"), 0x87: ("conv.ovf.u2.un", "none"),
    0x88: ("conv.ovf.u4.un", "none"), 0x89: ("conv.ovf.u8.un", "none"),
    0x8A: ("conv.ovf.i.un", "none"), 0x8B: ("conv.ovf.u.un", "none"),
    0x8C: ("box", "tok"), 0x8D: ("newarr", "tok"),
    0x8E: ("ldlen", "none"), 0x8F: ("ldelema", "tok"),
    0x90: ("ldelem.i1", "none"), 0x91: ("ldelem.u1", "none"),
    0x92: ("ldelem.i2", "none"), 0x93: ("ldelem.u2", "none"),
    0x94: ("ldelem.i4", "none"), 0x95: ("ldelem.u4", "none"),
    0x96: ("ldelem.i8", "none"), 0x97: ("ldelem.i", "none"),
    0x98: ("ldelem.r4", "none"), 0x99: ("ldelem.r8", "none"),
    0x9A: ("ldelem.ref", "none"), 0x9B: ("stelem.i", "none"),
    0x9C: ("stelem.i1", "none"), 0x9D: ("stelem.i2", "none"),
    0x9E: ("stelem.i4", "none"), 0x9F: ("stelem.i8", "none"),
    0xA0: ("stelem.r4", "none"), 0xA1: ("stelem.r8", "none"),
    0xA2: ("stelem.ref", "none"), 0xA3: ("ldelem", "tok"),
    0xA4: ("stelem", "tok"), 0xA5: ("unbox.any", "tok"),
    0xB3: ("conv.ovf.i1", "none"), 0xB4: ("conv.ovf.u1", "none"),
    0xB5: ("conv.ovf.i2", "none"), 0xB6: ("conv.ovf.u2", "none"),
    0xB7: ("conv.ovf.i4", "none"), 0xB8: ("conv.ovf.u4", "none"),
    0xB9: ("conv.ovf.i8", "none"), 0xBA: ("conv.ovf.u8", "none"),
    0xC2: ("refanyval", "tok"), 0xC3: ("ckfinite", "none"),
    0xC6: ("mkrefany", "tok"), 0xD0: ("ldtoken", "tok"),
    0xD1: ("conv.u2", "none"), 0xD2: ("conv.u1", "none"),
    0xD3: ("conv.i", "none"), 0xD4: ("conv.ovf.i", "none"),
    0xD5: ("conv.ovf.u", "none"), 0xD6: ("add.ovf", "none"),
    0xD7: ("add.ovf.un", "none"), 0xD8: ("mul.ovf", "none"),
    0xD9: ("mul.ovf.un", "none"), 0xDA: ("sub.ovf", "none"),
    0xDB: ("sub.ovf.un", "none"), 0xDC: ("endfinally", "none"),
    0xDD: ("leave", "br4"), 0xDE: ("leave.s", "br1"),
    0xDF: ("stind.i", "none"), 0xE0: ("conv.u", "none"),
}

OPS_FE = {
    0x00: ("arglist", "none"), 0x01: ("ceq", "none"),
    0x02: ("cgt", "none"), 0x03: ("cgt.un", "none"),
    0x04: ("clt", "none"), 0x05: ("clt.un", "none"),
    0x06: ("ldftn", "tok"), 0x07: ("ldvirtftn", "tok"),
    0x09: ("ldarg", "var2"), 0x0A: ("ldarga", "var2"),
    0x0B: ("starg", "var2"), 0x0C: ("ldloc", "var2"),
    0x0D: ("ldloca", "var2"), 0x0E: ("stloc", "var2"),
    0x0F: ("localloc", "none"), 0x11: ("endfilter", "none"),
    0x12: ("unaligned.", "u1"), 0x13: ("volatile.", "none"),
    0x14: ("tail.", "none"), 0x15: ("initobj", "tok"),
    0x16: ("constrained.", "tok"), 0x17: ("cpblk", "none"),
    0x18: ("initblk", "none"), 0x1A: ("rethrow", "none"),
    0x1C: ("sizeof", "tok"), 0x1D: ("refanytype", "none"),
    0x1E: ("readonly.", "none"),
}


def disassemble(asm, il):
    out = []
    i = 0
    n = len(il)
    while i < n:
        start = i
        b = il[i]
        i += 1
        if b == 0xFE:
            b2 = il[i]
            i += 1
            name, kind = OPS_FE.get(b2, (f"fe{b2:02x}", "none"))
        else:
            name, kind = OPS.get(b, (f"unk{b:02x}", "none"))

        arg = ""
        if kind == "none":
            pass
        elif kind == "u1":
            arg = str(il[i]); i += 1
        elif kind == "i1":
            arg = str(struct.unpack_from("<b", il, i)[0]); i += 1
        elif kind == "var2":
            arg = str(struct.unpack_from("<H", il, i)[0]); i += 2
        elif kind == "i4":
            arg = str(struct.unpack_from("<i", il, i)[0]); i += 4
        elif kind == "i8":
            arg = str(struct.unpack_from("<q", il, i)[0]); i += 8
        elif kind == "r4":
            arg = repr(struct.unpack_from("<f", il, i)[0]); i += 4
        elif kind == "r8":
            arg = repr(struct.unpack_from("<d", il, i)[0]); i += 8
        elif kind in ("tok", "str"):
            tok, = struct.unpack_from("<I", il, i); i += 4
            arg = asm.resolve_token(tok)
        elif kind == "br1":
            d = struct.unpack_from("<b", il, i)[0]; i += 1
            arg = f"IL_{i + d:04x}"
        elif kind == "br4":
            d = struct.unpack_from("<i", il, i)[0]; i += 4
            arg = f"IL_{i + d:04x}"
        elif kind == "switch":
            cnt, = struct.unpack_from("<I", il, i); i += 4
            tgts = []
            base = i + 4 * cnt
            for k in range(cnt):
                d = struct.unpack_from("<i", il, i)[0]; i += 4
                tgts.append(f"IL_{base + d:04x}")
            arg = ", ".join(tgts)
        out.append(f"IL_{start:04x}:  {name:<16s} {arg}")
    return out

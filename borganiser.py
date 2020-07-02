import re

BLOCK_START = "{"
BLOCK_END = "}"
LIST_SEP = ","

indent_level = 2

def skip_whitespace (txt, start):
    i = start
    while i < len(txt) and txt[i].isspace():
        i += 1
    return i

def read_next_block (txt, start, include_delims=False, start_delim=BLOCK_START, end_delim=BLOCK_END):
    buffer = ""
    i = skip_whitespace(txt, start) # Skip forward past any whitespace.
    # Raise exception if we don't get a block.
    if txt[i] != start_delim:
        raise SyntaxError(f"Cannot read a block when input stream does not start with a '{start_delim}' block open character. Instead, found '{txt[i]}'.")
    i += 1 # Next character to get inside the block.
    level = 1 # We're at level 1.
    while level > 0:
        if txt[i] in [start_delim, end_delim]: # Delimiter, so level change.
            level += 1 if txt[i] == start_delim else -1
            if include_delims or level > 0: # Include non-root delimiters always.
                buffer += txt[i]
        else:
            buffer += txt[i]
        i += 1
    return (buffer, i)

def read_next_value (txt, start, include_delims=False, start_delim=BLOCK_START, end_delim=BLOCK_END):
    buffer = ""
    i = skip_whitespace(txt, start) # Skip forward past any whitespace.
    if txt[i] == start_delim:
        # Simple, we have a block.
        buffer, i = read_next_block(txt, start, include_delims, start_delim, end_delim)
    elif txt[i] == "\"":
        # We have a quoted literal.
        i += 1 # Skip first quote.
        # Read up to next quote.
        while txt[i] != "\"": 
            buffer += txt[i]
            i += 1
        i += 1 # Skip final quote.
    else:
        # Standalone value outside a block.
        while txt[i] not in [LIST_SEP, end_delim] and not txt[i].isspace(): # Stop on list separator, block end or space.
            buffer += txt[i]
            i += 1
    return (buffer, i)

class BibtexField:
    key = None
    value = None
    def __init__ (self, key, captured):
        self.key = key
        self.value = captured
    def to_bibtex (self):
        return f"{self.key}={{{self.value}}}"

class BibtexEntry:
    type = None
    name = None
    fields = None
    def __init__(self, type, txt):
        self.fields = []
        self.type = type # Capture type.
        i = 0
        # Read in name.
        name = ""
        while txt[i] != LIST_SEP:
            name += txt[i]
            i += 1
        self.name = name.strip() # Strip whitespace from name.
        i += 1 # Skip comma.
        i = skip_whitespace(txt, i) # Skip whitespace.
        while i < len(txt):
            key = ""
            while txt[i] != "=":
                key += txt[i]
                i += 1
            key = key.strip() # Strip whitespace from key.
            i += 1 # Skip equals sign.
            i = skip_whitespace(txt, i) # Skip pre-value whitespace.
            value, i = read_next_value(txt, i) # Read next value.
            i += 1 # Skip the delimiter we hit.
            self.fields.append(BibtexField(key, value.strip())) # Strip whitespace from value and add entry.
            i = skip_whitespace(txt, i) # Skip whitespace, we're primed again.
    def sort_fields (self):
        self.fields.sort(key=lambda f: f.key)
    def to_bibtex (self):
        buffer = f"@{self.type.lower()}{{{self.name},\n  "
        buffer += ",\n  ".join([f.to_bibtex() for f in self.fields])
        buffer += "\n}"
        return buffer


class BibtexDocument:
    entries = None
    def __init__(self, txt):
        self.entries = []
        i = skip_whitespace(txt, 0) # Skip initial whitespace.
        while i < len(txt):
            # Every entry starts with an '@'.
            if txt[i] != "@":
                raise SyntaxError(f"Expected an '@' to start an item but got '{txt[i]}' instead.")
            i += 1 # Starting symbol found! Move on.
            # Read in type.
            type = ""
            while txt[i] != BLOCK_START:
                type += txt[i]
                i += 1
            # Read block.
            value, i = read_next_value(txt, i)
            # Add new entry.
            self.entries.append(BibtexEntry(type.strip(), value)) # Strip whitespace from type and add entry.
            i = skip_whitespace(txt, i) # Skip whitespace, we're primed again.
    def sort_entries (self):
        self.entries.sort(key=lambda e: e.name)
    def sort_fields (self):
        for entry in self.entries:
            entry.sort_fields()
    def to_bibtex (self):
        return "\n\n".join([e.to_bibtex() for e in self.entries])


file_content = None
with open("main.bib") as file:
    file_content = file.read()

doc = BibtexDocument(file_content)
doc.sort_entries()
#doc.sort_fields()
print(doc.to_bibtex())

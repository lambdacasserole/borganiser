""" A customisable script for organising and transforming BibTeX bibliographies.

Authors:
    Saul Johnson (saul.a.johnson@gmail.com)
Since:
    07/02/2024
"""

import sys

BLOCK_START = "{"
""" The BibTeX block start character.
"""

BLOCK_END = "}"
""" The BibTeX block end character.
"""

LIST_SEP = ","
""" The BibTeX list separator character.
"""


def skip_whitespace (source: str, start: int):
    """ Returns the index of the next non-whitespace character from a position in some source code.

    Args:
        source (str): The source code.
        start (int): The start index.
    Returns:
        int: The position of the next non-whitespace character after the start index in the string.
    """
    i = start
    while i < len(source) and source[i].isspace():
        i += 1
    return i


def read_next_block (
        source: str, 
        start: int, 
        include_delimiters: bool = False, 
        start_delimiter: str = BLOCK_START, 
        end_delimiter: str = BLOCK_END):
    """ Reads the next block in a BibTeX source file.
    
    Args:
        source (str): The BibTeX source code.
        start (int): The current position in the source code.
        include_delimiters (bool): Whether or not to include non-root-level delimiters.
        start_delimiter (str): The block start delimiter token (defaults to "{").
        end_delimiter (str): The block end delimiter token (defaults to "}").
    Returns:
        str: The source code of the next BibTeX block.
    """
    # Skip forward past any whitespace.
    i = skip_whitespace(source, start)

    # Raise exception if we don't get a block.
    if source[i] != start_delimiter:
        raise SyntaxError(f"Cannot read a block when input stream does not start with a '{start_delimiter}' block open character. Instead, found '{source[i]}'.")
    
    buffer = "" # Build buffer of text.
    i += 1 # Next character to get inside the block.
    level = 1 # We're at level 1.
    while level > 0:
        if source[i] in [start_delimiter, end_delimiter]:

            # We have a delimiter, so change the level.
            level += 1 if source[i] == start_delimiter else -1

            # Include non-root delimiters always.
            if include_delimiters or level > 0:
                buffer += source[i]
        else:
            buffer += source[i]
        i += 1

    # Return tuple of the buffer contents and its ending index.
    return (buffer, i)


def read_next_value (
        source: str,
        start: int, 
        include_delimiters: str = False, 
        start_delimiter: str = BLOCK_START, 
        end_delimiter: str = BLOCK_END):
    """ Reads the next value in a BibTeX source file (block or quoted literal).
    
    Args:
        source (str): The BibTeX source code.
        start (int): The current position in the source code.
        include_delimiters (bool): Whether or not to include non-root-level delimiters.
        start_delimiter (str): The block start delimiter token (defaults to "{").
        end_delimiter (str): The block end delimiter token (defaults to "}").
    Returns:
        str: The source code of the next BibTeX block.
    """
    # Skip forward past any whitespace.
    i = skip_whitespace(source, start)
    
    buffer = "" # Build buffer of text.
    if source[i] == start_delimiter:
        
        # Simple, we have a block.
        buffer, i = read_next_block(source, start, include_delimiters, start_delimiter, end_delimiter)
    elif source[i] == "\"":
        
        # We have a quoted literal. Skip first quote, read up to next quote and skip final quote.
        i += 1
        while source[i] != "\"": 
            buffer += source[i]
            i += 1
        i += 1
    else:
        
        # Standalone value outside a block.
        while source[i] not in [LIST_SEP, end_delimiter] and not source[i].isspace(): # Stop on list separator, block end or space.
            buffer += source[i]
            i += 1
            
    # Return tuple of the buffer contents and its ending index.
    return (buffer, i)


class BibtexField:
    """ Represents a BibTeX field.
    """
    
    def __init__ (self, key: str, value: str):
        """ Initializes a new instance of a BibTeX field.
        
        Args:
            key (str): The field key.
            value (str): The field value.
        """
        self.key = key
        self.value = value
        
    def to_bibtex (self):
        """ Converts this BibTeX field to its representation in source code.
        
        Returns:
            str: The source code representing this BibTeX field.
        """
        return f"{self.key}={{{self.value}}}"


class BibtexEntry:
    """ Represents a BibTeX entry.
    """
    
    def __init__ (self, type: str, source: str):
        """ Initializes a new instance of a BibTeX entry.
        
        Args:
            type (str): The entry type (e.g. inproceedings, article, misc).
            source (str): The source code comprising the entry.
        """
        
        # Initialize fields array.
        self.fields = []
        
        # Capture type.
        self.type = type
        
        # Initialize source code pointer.
        i = 0
        
        # Read in name.
        name = ""
        while source[i] != LIST_SEP:
            name += source[i]
            i += 1
            
        self.name = name.strip() # Strip whitespace from name.
        
        i += 1 # Skip comma.
        
        i = skip_whitespace(source, i) # Skip whitespace.
        
        # Process source.
        while i < len(source):
            
            # Read in key.
            key = ""
            while source[i] != "=":
                key += source[i]
                i += 1
                
             # Strip whitespace from key.
            key = key.strip()
            
            # Skip equals sign.
            i += 1 
            
            # Skip any pre-value whitespace.
            i = skip_whitespace(source, i)
            
            # Read next value.
            value, i = read_next_value(source, i)
            
            # Skip whatever delimiter we hit (usually a comma).
            i += 1
            
            # Strip whitespace from value and add field.
            self.fields.append(BibtexField(key, value.strip()))
            
            # Skip whitespace, we're primed to loop again.
            i = skip_whitespace(source, i)
            
    def sort_fields (self):
        """ Sorts all fields in the entry alphabetically.
        """
        self.fields.sort(key=lambda field: field.key)
        
    def to_bibtex (self):
        """ Converts this BibTeX entry to its representation in source code.
        
        Returns:
            str: The source code representing this BibTeX entry.
        """
        # Open entry.
        buffer = f"@{self.type.lower()}{{{self.name},\n  "
        
        # Add fields.
        buffer += ",\n  ".join([f.to_bibtex() for f in self.fields])
        
        # Close entry.
        buffer += "\n}"
        
        return buffer


class BibtexDocument:
    """ Represents a BibTeX document.
    """
    
    def __init__(self, source):
        """ Initializes a new instance of a BibTeX document.
        
        Args:
            source (str): The source code comprising the document.
        """
        self.entries = []
        
        # Skip initial whitespace.
        i = skip_whitespace(source, 0)
        
        # Loop over source.
        while i < len(source):
            
            # Every entry starts with an '@'.
            if source[i] != "@":
                raise SyntaxError(f"Expected an '@' to start an item but got '{source[i]}' instead.")
            
            # Starting symbol found! Move on.
            i += 1
            
            # Read in type.
            type = ""
            while source[i] != BLOCK_START:
                type += source[i]
                i += 1
                
            # Read block.
            value, i = read_next_value(source, i)
            
            # Strip whitespace from type and add entry.
            self.entries.append(BibtexEntry(type.strip(), value))
            
            # Skip whitespace, we're primed to loop again.
            i = skip_whitespace(source, i)
            
    def sort_entries (self):
        """ Sorts all entries in the document alphabetically.
        """
        self.entries.sort(key=lambda entry: entry.name)
        
    def sort_fields (self):
        """ Sorts all fields within entries in the document alphabetically.
        """
        for entry in self.entries:
            entry.sort_fields()
            
    def to_bibtex (self):
        """ Converts this BibTeX document to its representation in source code.
        
        Returns:
            str: The source code representing this BibTeX document.
        """
        return "\n\n".join([entry.to_bibtex() for entry in self.entries])


if __name__ == "__main__":
    
    # Read in file content.
    file_content = None
    with open("main.bib" if len(sys.argv) < 2 else sys.argv[-1]) as file:
        file_content = file.read()

    # Parse document.
    document = BibtexDocument(file_content)
    
    if '-f' in sys.argv:
        document.sort_fields() # Sort fields if '-f' flag passed.
    if '-S' not in sys.argv:
        document.sort_entries() # Skip sorting entries if '-S' flag passed.
        
    # Print document formatted.
    print(document.to_bibtex())

import sys
from pygments import highlight
from pygments.util import ClassNotFound as pygments_classNotFound
import scribus
from pygments.formatter import Formatter
from pygments.token import Token
import logging 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ScribusFormatter(Formatter):
    base_char_style = 'Code'
    def __init__(self, code_length, **options):
        logging.info("Initializing Code Formatter...")
        Formatter.__init__(self, **options)
        self.code_length = code_length

        logging.info(f"Received code with length {self.code_length}")

        self.character_styles = {
            Token.Text:                     self.base_char_style,
            Token.Keyword:                  self.base_char_style+'_keyword',
            Token.Keyword.Namespace:        self.base_char_style+'_keyword',
            Token.Punctuation:              self.base_char_style+'_punctuation',
            Token.Literal.String.Double:    self.base_char_style+'_literal',
            Token.Literal.String.Single:    self.base_char_style+'_literal',
            Token.Name:                     self.base_char_style,
            Token.Operator:                 self.base_char_style+'_operator',
            Token.Operator.Word:            self.base_char_style+'_operator_keyword',
            Token.Name.Builtin:             self.base_char_style+'_stdlib',
            Token.Literal.Number.Integer:   self.base_char_style+'_literal',
        }

        logging.info("Fetching styles and setting them if they don't exist.")
        self.existing_styles = scribus.getCharStyles()
        
        if self.base_char_style not in self.existing_styles:
            scribus.createCharStyle(self.base_char_style)

    def format(self, tokensource, outfile):
        current_frame = scribus.getSelectedObject()

        logging.info("Resetting the styles")
        scribus.setCharacterStyle(self.base_char_style)

        pos = 0
        for token_type, token_value in tokensource:
            token_length = len(token_value)

            # Define the start and end of the selection
            start_selection = pos
            end_selection = pos + token_length

            if end_selection > self.code_length:
                end_selection = self.code_length
                token_length = end_selection - start_selection 

            logging.info(f"Found token: token: {token_type}, token_value {token_value.strip()}, token_length: {token_length}, start_selection: {start_selection}, end_selection: {end_selection}")

            scribus.selectText(pos, token_length, current_frame)
            style_name = self.get_char_style(token_type)
            logging.info("Setting style...")
            scribus.setCharacterStyle(style_name, current_frame)

            pos += token_length

            if pos >= self.code_length:
                break

    def get_char_style(self, token_type):
        style_name = self.character_styles.get(token_type, self.base_char_style)
        logging.info(f"Identified style: {style_name}")

        if style_name not in self.existing_styles:
            color = self.style.style_for_token(token_type).get('color')
            self.existing_styles.append(style_name)
            arguments = {}
            if color:
                color_values = [int(color[i:i+2], 16) for i in range(0, 6, 2)]
                color_values = [min(255, value) for value in color_values]
                scribus.defineColorRGB(style_name, *color_values)
                arguments['fillcolor'] = style_name
            # TODO: add other style elements (underline, italic, bold)
            # (bold and italic won't be easy)
            # TODO: add the parent_style to the API
            scribus.createCharStyle(style_name, **arguments)

        return style_name

logging.info("Starting Code Formatter for Scribus!")

code = scribus.getAllText()

logging.info("Text fetched.")

# TODO: read the item's attributes
attribute = ''
for a in scribus.getObjectAttributes():
    if a['Name'] == 'syntax-highlight':
        attribute = a['Value']
        logging.info(f"syntax-highlight attribute set by user, value is now {attribute}")

if attribute != '':
    try:
        logging.info(f"Fetching Pygments lexer using user provided attribute...")
        from pygments.lexers import get_lexer_by_name
        lexer = get_lexer_by_name(attribute)
    except pygments_classNotFound:
        logging.error(f"Lexer attribute set, but not recognized by Pygments.")
        pass
else:
    from pygments.lexers import guess_lexer
    try:
        logging.info(f"No user provided attribute found. Guessing Pygments lexer...")
        lexer = guess_lexer(code)
    except pygments_classNotFound:
        logging.error(f"Lexer not identified! Parsing cannot work")
        pass

if not lexer:
    sys.exit()

highlight(code, lexer, ScribusFormatter(len(code)))
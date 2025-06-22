import win32com.client

wdAlignParagraphLeft = 0
wdAlignParagraphCenter = 1
wdAlignParagraphRight = 2
wdAlignParagraphJustify = 3


class WordController:
    def __init__(self):
        try:
            self.word = win32com.client.Dispatch("Word.Application")
            self.word.Visible = True
            if not self.word.ActiveDocument:
                self.word.Documents.Add()
        except Exception as e:
            print(f"Ошибка подключения к Word: {e}")
            self.word = None

    def apply_formatting(self, command):
        if not self.word:
            return

        try:
            if not self.word.ActiveDocument:
                print("Нет активного документа")
                return

            selection = self.word.Selection
            if not selection or not selection.Text.strip():
                print("Нет выделенного текста")
                return

            if command == "Полужирный":
                selection.Font.Bold = not selection.Font.Bold
            elif command == "Курсив":
                selection.Font.Italic = not selection.Font.Italic
            elif command == "Подчёркнутый":
                selection.Font.Underline = not selection.Font.Underline
            elif command == "Зачёркнутый":
                selection.Font.StrikeThrough = not selection.Font.StrikeThrough
            elif command == "Удалить форматирование":
                selection.Font.Bold = False
                selection.Font.Italic = False
                selection.Font.Underline = False
                selection.Font.StrikeThrough = False
            elif command == "Верхний индекс":
                selection.Font.Superscript = not selection.Font.Superscript
                selection.Font.Subscript = False
            elif command == "Нижний индекс":
                selection.Font.Subscript = not selection.Font.Subscript
                selection.Font.Superscript = False
            elif command == "По левому краю":
                selection.Paragraphs.Alignment = wdAlignParagraphLeft
            elif command == "По центру":
                selection.Paragraphs.Alignment = wdAlignParagraphCenter
            elif command == "По правому краю":
                selection.Paragraphs.Alignment = wdAlignParagraphRight
            elif command == "По ширине":
                selection.Paragraphs.Alignment = wdAlignParagraphJustify
            elif command == "Ненумерованный список":
                range_obj = selection.Range
                list_format = range_obj.ListFormat
                if list_format.ListLevelNumber != 0:
                    list_format.RemoveNumbers()
                list_format.ApplyBulletDefault()
            elif command == "Нумерованный список":
                range_obj = selection.Range
                list_format = range_obj.ListFormat
                if list_format.ListLevelNumber != 0:
                    list_format.RemoveNumbers()
                list_format.ApplyNumberDefault()
            elif command == "Увеличить отступ":
                selection.ParagraphFormat.LeftIndent += 36
            elif command == "Уменьшить отступ":
                selection.ParagraphFormat.LeftIndent -= 36
            elif command == "Изменить регистр":
                original_text = selection.Text
                paragraph_mark = ""

                if original_text and original_text.endswith("\r"):
                    paragraph_mark = original_text[-1]
                    text_to_process = original_text[:-1]
                else:
                    text_to_process = original_text

                letters = [c for c in text_to_process if c.isalpha()]
                if not letters:
                    new_text = text_to_process.title()
                elif all(c.islower() for c in letters):
                    new_text = text_to_process.title()
                elif letters[0].isupper() and all(c.islower() for c in letters[1:]):
                    new_text = text_to_process.upper()
                elif all(c.isupper() for c in letters):
                    new_text = text_to_process.lower()
                else:
                    new_text = text_to_process.lower()

                new_text += paragraph_mark
                selection.Text = new_text
        except Exception as e:
            print(f"Ошибка форматирования Word: {e}")

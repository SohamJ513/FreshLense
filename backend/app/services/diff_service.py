import difflib
from typing import List
from ..schemas.diff import ContentChange, ChangeType

class DiffService:
    def compare_text(self, old_text: str, new_text: str) -> List[ContentChange]:
        """Compare two text versions and return changes"""
        changes = []
        
        # Use difflib to get detailed differences
        differ = difflib.SequenceMatcher(None, old_text.splitlines(), new_text.splitlines())
        
        for opcode in differ.get_opcodes():
            tag, i1, i2, j1, j2 = opcode
            
            old_lines = old_text.splitlines()[i1:i2]
            new_lines = new_text.splitlines()[j1:j2]
            
            if tag == 'replace':
                changes.append(ContentChange(
                    change_type=ChangeType.MODIFIED,
                    old_content='\n'.join(old_lines),
                    new_content='\n'.join(new_lines),
                    line_range_old=(i1, i2),
                    line_range_new=(j1, j2)
                ))
            elif tag == 'delete':
                changes.append(ContentChange(
                    change_type=ChangeType.REMOVED,
                    old_content='\n'.join(old_lines),
                    new_content='',
                    line_range_old=(i1, i2),
                    line_range_new=(j1, j1)
                ))
            elif tag == 'insert':
                changes.append(ContentChange(
                    change_type=ChangeType.ADDED,
                    old_content='',
                    new_content='\n'.join(new_lines),
                    line_range_old=(i1, i1),
                    line_range_new=(j1, j2)
                ))
        
        return changes
    
    def generate_html_diff(self, old_text: str, new_text: str) -> str:
        """Generate HTML showing differences with color coding"""
        diff = difflib.HtmlDiff(wrapcolumn=80)
        return diff.make_file(
            old_text.splitlines(),
            new_text.splitlines(),
            fromdesc="Previous Version",
            todesc="Current Version",
            context=True,
            numlines=3
        )
    
    def calculate_change_metrics(self, old_text: str, new_text: str) -> dict:
        """Calculate change statistics"""
        words_old = old_text.split()
        words_new = new_text.split()
        
        added_words = set(words_new) - set(words_old)
        removed_words = set(words_old) - set(words_new)
        
        return {
            "words_added": len(added_words),
            "words_removed": len(removed_words),
            "total_words_old": len(words_old),
            "total_words_new": len(words_new),
            "change_percentage": abs(len(words_new) - len(words_old)) / max(len(words_old), 1) * 100
        }
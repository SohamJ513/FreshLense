import difflib
import re
import hashlib
from typing import List, Tuple, Dict, Any, Optional
from html import escape
from ..schemas.diff import ContentChange, ChangeType

class DiffService:
    def compare_text(self, old_text: str, new_text: str) -> List[ContentChange]:
        """Compare two text versions and return changes with proper highlighting"""
        changes = []
        
        # Clean the texts
        old_text = old_text or ""
        new_text = new_text or ""
        
        # If one is empty, treat as full add/remove
        if not old_text and new_text:
            return [ContentChange(
                change_type=ChangeType.ADDED,
                old_content="",
                new_content=new_text,
                line_range_old=(0, 0),
                line_range_new=(0, len(new_text.splitlines())),
                context_before="",
                context_after="",
                highlighted_old="",
                highlighted_new=self._highlight_added_text(new_text)
            )]
        
        if old_text and not new_text:
            return [ContentChange(
                change_type=ChangeType.REMOVED,
                old_content=old_text,
                new_content="",
                line_range_old=(0, len(old_text.splitlines())),
                line_range_new=(0, 0),
                context_before="",
                context_after="",
                highlighted_old=self._highlight_removed_text(old_text),
                highlighted_new=""
            )]
        
        # Split into lines for line-by-line comparison
        old_lines = old_text.splitlines(keepends=True)  # Keep line endings
        new_lines = new_text.splitlines(keepends=True)
        
        # Use difflib for line-level comparison
        differ = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            old_chunk = old_lines[i1:i2]
            new_chunk = new_lines[j1:j2]
            
            # Get context (2 lines before and after)
            context_before_old = old_lines[max(0, i1-2):i1]
            context_after_old = old_lines[i2:min(len(old_lines), i2+2)]
            context_before_new = new_lines[max(0, j1-2):j1]
            context_after_new = new_lines[j2:min(len(new_lines), j2+2)]
            
            # Convert chunks to strings
            old_chunk_str = ''.join(old_chunk)
            new_chunk_str = ''.join(new_chunk)
            
            # Get context as strings
            context_before_str = ''.join(context_before_old + context_before_new)
            context_after_str = ''.join(context_after_old + context_after_new)
            
            if tag == 'replace':
                # For replacements, do word-level diff within the chunk
                highlighted_old, highlighted_new = self._highlight_word_changes(
                    old_chunk_str, new_chunk_str
                )
                
                changes.append(ContentChange(
                    change_type=ChangeType.MODIFIED,
                    old_content=old_chunk_str,
                    new_content=new_chunk_str,
                    line_range_old=(i1, i2),
                    line_range_new=(j1, j2),
                    context_before=context_before_str,
                    context_after=context_after_str,
                    highlighted_old=highlighted_old,
                    highlighted_new=highlighted_new,
                    change_summary=self._get_change_summary(old_chunk_str, new_chunk_str)
                ))
                
            elif tag == 'delete':
                changes.append(ContentChange(
                    change_type=ChangeType.REMOVED,
                    old_content=old_chunk_str,
                    new_content="",
                    line_range_old=(i1, i2),
                    line_range_new=(j1, j1),
                    context_before=context_before_str,
                    context_after=context_after_str,
                    highlighted_old=self._highlight_removed_text(old_chunk_str),
                    highlighted_new="",
                    change_summary=f"Removed {len(old_chunk)} lines"
                ))
                
            elif tag == 'insert':
                changes.append(ContentChange(
                    change_type=ChangeType.ADDED,
                    old_content="",
                    new_content=new_chunk_str,
                    line_range_old=(i1, i1),
                    line_range_new=(j1, j2),
                    context_before=context_before_str,
                    context_after=context_after_str,
                    highlighted_old="",
                    highlighted_new=self._highlight_added_text(new_chunk_str),
                    change_summary=f"Added {len(new_chunk)} lines"
                ))
        
        return changes
    
    def _highlight_word_changes(self, old_text: str, new_text: str) -> Tuple[str, str]:
        """Highlight word-level changes between two texts"""
        # Split into words for detailed comparison
        old_words = re.findall(r'\S+|\s+', old_text)  # Keep whitespace
        new_words = re.findall(r'\S+|\s+', new_text)
        
        # Compare word sequences
        differ = difflib.SequenceMatcher(None, old_words, new_words)
        
        highlighted_old_words = []
        highlighted_new_words = []
        
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'equal':
                highlighted_old_words.extend(old_words[i1:i2])
                highlighted_new_words.extend(new_words[j1:j2])
            elif tag == 'replace':
                # Highlight removed words in old text
                for word in old_words[i1:i2]:
                    if word.strip():  # Only highlight non-whitespace
                        highlighted_old_words.append(f'<span class="removed-word">{escape(word)}</span>')
                    else:
                        highlighted_old_words.append(word)
                
                # Highlight added words in new text
                for word in new_words[j1:j2]:
                    if word.strip():  # Only highlight non-whitespace
                        highlighted_new_words.append(f'<span class="added-word">{escape(word)}</span>')
                    else:
                        highlighted_new_words.append(word)
            elif tag == 'delete':
                for word in old_words[i1:i2]:
                    if word.strip():
                        highlighted_old_words.append(f'<span class="removed-word">{escape(word)}</span>')
                    else:
                        highlighted_old_words.append(word)
            elif tag == 'insert':
                for word in new_words[j1:j2]:
                    if word.strip():
                        highlighted_new_words.append(f'<span class="added-word">{escape(word)}</span>')
                    else:
                        highlighted_new_words.append(word)
        
        return ''.join(highlighted_old_words), ''.join(highlighted_new_words)
    
    def _highlight_added_text(self, text: str) -> str:
        """Highlight added text with green background"""
        lines = text.splitlines(keepends=True)
        highlighted_lines = []
        
        for line in lines:
            if line.strip():
                # Split line into words and highlight each word
                words = re.findall(r'\S+|\s+', line)
                highlighted_words = []
                for word in words:
                    if word.strip():
                        highlighted_words.append(f'<span class="added-word">{escape(word)}</span>')
                    else:
                        highlighted_words.append(word)
                highlighted_lines.append(''.join(highlighted_words))
            else:
                highlighted_lines.append(line)
        
        return ''.join(highlighted_lines)
    
    def _highlight_removed_text(self, text: str) -> str:
        """Highlight removed text with red strikethrough"""
        lines = text.splitlines(keepends=True)
        highlighted_lines = []
        
        for line in lines:
            if line.strip():
                # Split line into words and highlight each word
                words = re.findall(r'\S+|\s+', line)
                highlighted_words = []
                for word in words:
                    if word.strip():
                        highlighted_words.append(f'<span class="removed-word">{escape(word)}</span>')
                    else:
                        highlighted_words.append(word)
                highlighted_lines.append(''.join(highlighted_words))
            else:
                highlighted_lines.append(line)
        
        return ''.join(highlighted_lines)
    
    def _get_change_summary(self, old_text: str, new_text: str) -> str:
        """Generate a summary of changes"""
        old_words = old_text.split()
        new_words = new_text.split()
        
        added = set(new_words) - set(old_words)
        removed = set(old_words) - set(new_words)
        
        return f"Changed {len(added)} words added, {len(removed)} words removed"
    
    def generate_html_diff(self, old_text: str, new_text: str) -> str:
        """Generate HTML showing differences with color coding"""
        # Use custom highlighting instead of default HtmlDiff
        changes = self.compare_text(old_text, new_text)
        
        if not changes:
            return f'<div class="no-changes">No changes detected</div>'
        
        html_parts = ['<div class="diff-container">']
        
        for change in changes:
            html_parts.append(f'<div class="change-item {change.change_type.value}">')
            
            if change.change_type == ChangeType.ADDED:
                html_parts.append('<div class="change-header">➕ Added Content</div>')
                html_parts.append(f'<div class="new-content">{change.highlighted_new}</div>')
                
            elif change.change_type == ChangeType.REMOVED:
                html_parts.append('<div class="change-header">➖ Removed Content</div>')
                html_parts.append(f'<div class="old-content">{change.highlighted_old}</div>')
                
            elif change.change_type == ChangeType.MODIFIED:
                html_parts.append('<div class="change-header">✏️ Modified Content</div>')
                html_parts.append('<div class="modified-comparison">')
                html_parts.append('<div class="comparison-column">')
                html_parts.append('<h4>Previous Version</h4>')
                html_parts.append(f'<div class="old-content">{change.highlighted_old}</div>')
                html_parts.append('</div>')
                html_parts.append('<div class="comparison-column">')
                html_parts.append('<h4>Current Version</h4>')
                html_parts.append(f'<div class="new-content">{change.highlighted_new}</div>')
                html_parts.append('</div>')
                html_parts.append('</div>')
            
            if change.context_before:
                html_parts.append(f'<div class="context-before">...{escape(change.context_before[-100:])}</div>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        # Add CSS
        html_parts.append('''
        <style>
        .diff-container {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        .change-item {
            margin: 15px 0;
            border-radius: 4px;
            overflow: hidden;
        }
        .change-header {
            padding: 8px 12px;
            font-weight: bold;
            font-size: 14px;
        }
        .change-item.added .change-header {
            background-color: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        .change-item.removed .change-header {
            background-color: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        .change-item.modified .change-header {
            background-color: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffc107;
        }
        .old-content, .new-content {
            padding: 10px 12px;
            background-color: #f8f9fa;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .modified-comparison {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .comparison-column h4 {
            margin: 0 0 8px 0;
            font-size: 13px;
            color: #6c757d;
        }
        .added-word {
            background-color: #c3e6cb;
            padding: 1px 2px;
            border-radius: 2px;
            color: #155724;
        }
        .removed-word {
            background-color: #f5c6cb;
            padding: 1px 2px;
            border-radius: 2px;
            color: #721c24;
            text-decoration: line-through;
        }
        .context-before {
            font-size: 12px;
            color: #6c757d;
            padding: 4px 12px;
            background-color: #e9ecef;
            font-style: italic;
        }
        .no-changes {
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-style: italic;
        }
        </style>
        ''')
        
        return '\n'.join(html_parts)
    
    def calculate_change_metrics(self, old_text: str, new_text: str) -> Dict[str, Any]:
        """✅ ENHANCED: Calculate comprehensive change statistics for versioning"""
        old_text = old_text or ""
        new_text = new_text or ""
        
        # Basic word metrics
        words_old = old_text.split()
        words_new = new_text.split()
        
        # Character-level similarity
        char_similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()
        
        # Line-level changes
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        
        # Word-level changes (more accurate than set difference)
        word_differ = difflib.SequenceMatcher(None, words_old, words_new)
        word_changes = sum(size for tag, i1, i2, j1, j2 in word_differ.get_opcodes() 
                          if tag != 'equal')
        
        # Line-level structural changes
        line_differ = difflib.SequenceMatcher(None, old_lines, new_lines)
        line_changes = sum(size for tag, i1, i2, j1, j2 in line_differ.get_opcodes() 
                          if tag != 'equal')
        
        # Calculate percentages
        total_words_old = len(words_old)
        total_words_new = len(words_new)
        total_lines_old = len(old_lines)
        total_lines_new = len(new_lines)
        
        word_change_percentage = (word_changes / max(total_words_old, total_words_new, 1)) * 100
        line_change_percentage = (line_changes / max(total_lines_old, total_lines_new, 1)) * 100
        
        # ✅ ADDED: Technical keyword detection (for tech blogs)
        tech_keywords = [
            'security', 'vulnerability', 'update', 'critical', 'bug', 'fix',
            'release', 'version', 'deprecated', 'breaking', 'important',
            'urgent', 'warning', 'alert', 'patch', 'exploit', 'risk',
            'cve-', 'mitigation', 'workaround', 'upgrade', 'downgrade',
            'compatibility', 'performance', 'memory', 'cpu', 'storage',
            'latency', 'throughput', 'regression', 'feature', 'api'
        ]
        
        old_lower = old_text.lower()
        new_lower = new_text.lower()
        
        keyword_changes = 0
        keyword_details = []
        for keyword in tech_keywords:
            old_has = keyword in old_lower
            new_has = keyword in new_lower
            if old_has != new_has:
                keyword_changes += 1
                keyword_details.append({
                    'keyword': keyword,
                    'action': 'added' if new_has and not old_has else 'removed',
                    'context': self._extract_keyword_context(keyword, old_text if old_has else new_text)
                })
        
        # ✅ ADDED: Calculate significance score components
        significance_components = {
            'character_similarity': char_similarity * 100,
            'word_change_ratio': word_change_percentage,
            'line_change_ratio': line_change_percentage,
            'keyword_changes': keyword_changes,
            'structural_changes': line_change_percentage * 0.5  # Weighted
        }
        
        # Calculate overall significance score (0-1)
        significance_score = self._calculate_significance_score(significance_components)
        
        return {
            # Basic metrics
            "words_added": len(set(words_new) - set(words_old)),
            "words_removed": len(set(words_old) - set(words_new)),
            "total_words_old": total_words_old,
            "total_words_new": total_words_new,
            "similarity_score": char_similarity * 100,
            "change_percentage": (1 - char_similarity) * 100,
            "lines_added": len(new_lines) - len(old_lines) if len(new_lines) > len(old_lines) else 0,
            "lines_removed": len(old_lines) - len(new_lines) if len(old_lines) > len(new_lines) else 0,
            
            # ✅ ENHANCED METRICS
            "word_change_percentage": word_change_percentage,
            "line_change_percentage": line_change_percentage,
            "character_similarity": char_similarity * 100,
            "structural_change_count": line_changes,
            "word_change_count": word_changes,
            
            # ✅ SMART VERSIONING METRICS
            "significance_score": significance_score,
            "keyword_changes": keyword_changes,
            "keyword_details": keyword_details,
            "significance_components": significance_components,
            
            # Content hashes for quick comparison
            "content_hash_old": self.calculate_content_hash(old_text) if old_text else None,
            "content_hash_new": self.calculate_content_hash(new_text) if new_text else None,
            "checksum_old": self.calculate_quick_checksum(old_text) if old_text else None,
            "checksum_new": self.calculate_quick_checksum(new_text) if new_text else None
        }
    
    def _calculate_significance_score(self, components: Dict[str, float]) -> float:
        """Calculate overall change significance score (0-1)"""
        # Weights for different components
        weights = {
            'character_similarity': 0.3,      # 30% weight
            'word_change_ratio': 0.4,         # 40% weight
            'line_change_ratio': 0.2,         # 20% weight
            'keyword_changes': 0.1,           # 10% weight
            'structural_changes': 0.1         # 10% weight
        }
        
        score = 0.0
        
        # Normalize character similarity (higher similarity = lower significance)
        char_sim = components.get('character_similarity', 100)
        score += ((100 - min(char_sim, 100)) / 100) * weights['character_similarity']
        
        # Normalize word change ratio
        word_change = min(components.get('word_change_ratio', 0), 100)
        score += (word_change / 100) * weights['word_change_ratio']
        
        # Normalize line change ratio
        line_change = min(components.get('line_change_ratio', 0), 100)
        score += (line_change / 100) * weights['line_change_ratio']
        
        # Keyword changes (each keyword change adds to score)
        keyword_changes = min(components.get('keyword_changes', 0), 10)  # Cap at 10
        score += (keyword_changes / 10) * weights['keyword_changes']
        
        # Structural changes
        structural = min(components.get('structural_changes', 0), 100)
        score += (structural / 100) * weights['structural_changes']
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _extract_keyword_context(self, keyword: str, text: str, context_chars: int = 100) -> str:
        """Extract context around a keyword"""
        if not text:
            return ""
        
        lower_text = text.lower()
        idx = lower_text.find(keyword)
        if idx == -1:
            return ""
        
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(keyword) + context_chars)
        
        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context
    
    def calculate_content_hash(self, text: str) -> str:
        """✅ ADDED: Calculate SHA256 hash of content for accurate comparison"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def calculate_quick_checksum(self, text: str) -> str:
        """✅ ADDED: Calculate MD5 checksum for very fast comparison"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def analyze_change_significance(self, old_text: str, new_text: str, 
                                   min_threshold: float = 0.05) -> Dict[str, Any]:
        """✅ ADDED: Comprehensive analysis of change significance"""
        # Quick checks first
        if not old_text and new_text:
            return {
                "store": True,
                "reason": "First version",
                "score": 1.0,
                "significant": True,
                "analysis_type": "first_version"
            }
        
        if old_text == new_text:
            return {
                "store": False,
                "reason": "Identical content",
                "score": 0.0,
                "significant": False,
                "analysis_type": "identical"
            }
        
        # Quick checksum comparison
        if self.calculate_quick_checksum(old_text) == self.calculate_quick_checksum(new_text):
            return {
                "store": False,
                "reason": "Identical checksum",
                "score": 0.0,
                "significant": False,
                "analysis_type": "identical_checksum"
            }
        
        # Calculate detailed metrics
        metrics = self.calculate_change_metrics(old_text, new_text)
        significance_score = metrics.get("significance_score", 0.0)
        
        # Determine if significant enough
        significant = significance_score >= min_threshold
        
        reasons = []
        if significance_score >= 0.7:
            reasons.append("Major content restructuring")
        elif significance_score >= 0.5:
            reasons.append("Substantial content changes")
        elif significance_score >= 0.3:
            reasons.append("Moderate content updates")
        elif significance_score >= 0.1:
            reasons.append("Minor content tweaks")
        else:
            reasons.append("Insignificant changes")
        
        # Add specific reasons based on metrics
        if metrics.get("keyword_changes", 0) > 0:
            reasons.append(f"{metrics['keyword_changes']} technical keywords changed")
        
        if metrics.get("word_change_percentage", 0) > 20:
            reasons.append(f"High word change ({metrics['word_change_percentage']:.1f}%)")
        elif metrics.get("word_change_percentage", 0) > 10:
            reasons.append(f"Moderate word change ({metrics['word_change_percentage']:.1f}%)")
        
        return {
            "store": significant,
            "reason": "; ".join(reasons),
            "score": significance_score,
            "significant": significant,
            "metrics": metrics,
            "hash": self.calculate_content_hash(new_text),
            "checksum": self.calculate_quick_checksum(new_text),
            "analysis_type": "detailed_analysis",
            "threshold_used": min_threshold
        }
    
    def get_side_by_side_diff(self, old_text: str, new_text: str) -> List[Dict[str, Any]]:
        """Get side-by-side diff for line-by-line comparison"""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        differ = difflib.SequenceMatcher(None, old_lines, new_lines)
        side_by_side = []
        
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'equal':
                for i in range(i1, i2):
                    side_by_side.append({
                        "old_line": old_lines[i],
                        "new_line": new_lines[j1 + (i - i1)],
                        "type": "unchanged",
                        "old_line_num": i + 1,
                        "new_line_num": j1 + (i - i1) + 1
                    })
            
            elif tag == 'replace':
                max_len = max(i2 - i1, j2 - j1)
                for k in range(max_len):
                    old_line = old_lines[i1 + k] if i1 + k < i2 else ""
                    new_line = new_lines[j1 + k] if j1 + k < j2 else ""
                    
                    # Highlight word changes within the line
                    if old_line and new_line:
                        highlighted_old, highlighted_new = self._highlight_word_changes(old_line, new_line)
                        side_by_side.append({
                            "old_line": highlighted_old,
                            "new_line": highlighted_new,
                            "type": "modified",
                            "old_line_num": i1 + k + 1 if old_line else None,
                            "new_line_num": j1 + k + 1 if new_line else None
                        })
                    elif old_line:
                        side_by_side.append({
                            "old_line": self._highlight_removed_text(old_line),
                            "new_line": "",
                            "type": "removed",
                            "old_line_num": i1 + k + 1,
                            "new_line_num": None
                        })
                    elif new_line:
                        side_by_side.append({
                            "old_line": "",
                            "new_line": self._highlight_added_text(new_line),
                            "type": "added",
                            "old_line_num": None,
                            "new_line_num": j1 + k + 1
                        })
            
            elif tag == 'delete':
                for k in range(i1, i2):
                    side_by_side.append({
                        "old_line": self._highlight_removed_text(old_lines[k]),
                        "new_line": "",
                        "type": "removed",
                        "old_line_num": k + 1,
                        "new_line_num": None
                    })
            
            elif tag == 'insert':
                for k in range(j1, j2):
                    side_by_side.append({
                        "old_line": "",
                        "new_line": self._highlight_added_text(new_lines[k]),
                        "type": "added",
                        "old_line_num": None,
                        "new_line_num": k + 1
                    })
        
        return side_by_side
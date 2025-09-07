#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
統合版JSP解析ツール
JSPファイルの包括的な解析を行い、CSV、Markdown、JSONフォーマットでレポートを生成します。
"""

import os
import csv
import re
import sys
import json
import glob
import argparse
import networkx as nx
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False
    print("警告: BeautifulSoupがインストールされていません。HTML解析機能が制限されます。")
    print("インストールするには: pip install beautifulsoup4")

try:
    import xml.etree.ElementTree as ET
    HAS_XML = True
except ImportError:
    HAS_XML = False

try:
    import javalang
    HAS_JAVALANG = True
except Exception:
    HAS_JAVALANG = False


class UnifiedJSPAnalyzer:
    """統合版JSPファイル解析クラス"""
    
    def __init__(self, project_dir, verbose=False):
        self.project_dir = project_dir
        self.verbose = verbose
        
        # ファイル情報
        self.jsp_files = {}  # JSPファイルの基本情報
        
        # 抽出データ
        self.directives = defaultdict(list)  # ディレクティブ情報
        self.includes = defaultdict(list)  # インクルード関係
        self.tag_libraries = defaultdict(list)  # タグライブラリ
        self.scriptlets = defaultdict(list)  # スクリプトレット
        self.expressions = defaultdict(list)  # JSP式
        self.declarations = defaultdict(list)  # 宣言
        self.actions = defaultdict(list)  # JSPアクション
        self.el_expressions = defaultdict(list)  # EL式
        self.jstl_usage = defaultdict(list)  # JSTL使用状況
        self.custom_tags = defaultdict(list)  # カスタムタグ
        self.forms = defaultdict(list)  # フォーム情報
        self.session_usage = defaultdict(list)  # セッション使用
        self.request_usage = defaultdict(list)  # リクエスト使用
        self.response_usage = defaultdict(list)  # レスポンス使用
        self.db_operations = defaultdict(list)  # DB操作
        self.dependencies = defaultdict(list)  # 依存関係
        self.css_classes = defaultdict(set)  # CSSクラス
        self.js_functions = defaultdict(set)  # JavaScript関数
        
        # メトリクス
        self.metrics = {}  # 各ファイルのメトリクス
        self.complexity_metrics = {}  # 複雑度メトリクス
        self.coupling_metrics = {}  # 結合度メトリクス
        self.security_issues = defaultdict(list)  # セキュリティ問題
        
        # パターン解析
        self.html_patterns = {}  # HTML構造パターン
        self.java_patterns = {}  # Javaコードパターン
        
        # 問題検出
        self.issues = defaultdict(list)  # 検出された問題
        
        # 依存関係グラフ
        self.dependency_graph = nx.DiGraph()

    def log(self, message):
        """ログ出力"""
        if self.verbose:
            print(message)

    def scan_files(self):
        """JSPファイルをスキャン"""
        patterns = [
            os.path.join(self.project_dir, '**', '*.jsp'),
            os.path.join(self.project_dir, '**', '*.jspf'),
            os.path.join(self.project_dir, '**', '*.tag'),
            os.path.join(self.project_dir, '**', '*.tagx')
        ]
        
        all_files = []
        for pattern in patterns:
            all_files.extend(glob.glob(pattern, recursive=True))
        
        # build、target、distディレクトリを除外（WEB-INF/tagsは含める）
        filtered_files = []
        for f in all_files:
            exclude = False
            for exclude_dir in ['build', 'target', 'dist']:
                if os.sep + exclude_dir + os.sep in f:
                    if 'WEB-INF' not in f:  # WEB-INF配下は除外しない
                        exclude = True
                        break
            if not exclude:
                filtered_files.append(f)
        
        return filtered_files

    def analyze_project(self):
        """プロジェクト全体を解析"""
        files = self.scan_files()
        
        print(f"{len(files)}個のJSPファイルを解析中...")
        
        # ファイルごとに解析
        for i, file_path in enumerate(files, 1):
            if self.verbose:
                print(f"[{i}/{len(files)}] {file_path} を解析中...")
            else:
                if i % 10 == 0:
                    print(f"  {i}/{len(files)} ファイル処理済み...")
            
            self.analyze_file(file_path)
        
        # 依存関係とパターン解析
        print("依存関係グラフを構築中...")
        self.build_dependency_graph()
        
        print("結合度メトリクスを計算中...")
        self.calculate_coupling_metrics()
        
        if HAS_BEAUTIFULSOUP:
            print("HTMLパターンを解析中...")
            self._analyze_html_patterns()
        
        print("Javaパターンを解析中...")
        self._analyze_java_patterns()
        
        print("問題パターンを検出中...")
        self._identify_issue_patterns()
        
        print(f"\n解析完了: {len(self.jsp_files)}個のJSPファイルを処理しました")

    def analyze_file(self, file_path):
        """単一のJSPファイルを解析"""
        content = self._read_file_content(file_path)
        if content is None:
            return
        
        relative_path = os.path.relpath(file_path, self.project_dir)
        file_id = relative_path.replace('\\', '/').replace('.', '_')
        
        # ファイル情報を保存
        self.jsp_files[file_id] = {
            'path': relative_path,
            'full_path': file_path,
            'size': os.path.getsize(file_path),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 各要素を抽出
            self._extract_directives(content, file_id)
            self._extract_includes(content, file_id)
            self._extract_scriptlets(content, file_id)
            self._extract_expressions(content, file_id)
            self._extract_declarations(content, file_id)
            self._extract_actions(content, file_id)
            self._extract_el_expressions(content, file_id)
            self._extract_jstl_usage(content, file_id)
            self._extract_custom_tags(content, file_id)
            self._extract_forms(content, file_id)
            self._extract_implicit_objects(content, file_id)
            self._extract_db_operations(content, file_id)
            self._extract_frontend_elements(content, file_id)
            
            # メトリクスを計算
            self._calculate_file_metrics(content, file_id)
            
            # セキュリティ問題を検出
            self._detect_security_issues(content, file_id)
            
        except Exception as e:
            self.log(f"警告: {file_path} の解析中にエラーが発生しました: {e}")
            self.issues[file_id].append({
                'type': 'analysis_error',
                'message': f"ファイル解析中にエラーが発生: {str(e)}"
            })

    def _read_file_content(self, file_path):
        """ファイル内容を読み込み（複数のエンコーディングを試行）"""
        encodings = ['utf-8', 'shift-jis', 'euc-jp', 'iso-2022-jp', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.log(f"警告: {file_path} を読み込めませんでした: {e}")
                return None
        
        self.log(f"警告: {file_path} はどのエンコーディングでも読み込めませんでした")
        return None

    def _parse_attributes(self, text: str) -> Dict[str, str]:
        """属性文字列を安定的にパースして辞書で返す。クォートあり/なしの両方に対応。"""
        attrs: Dict[str, str] = {}
        # matches key="value" or key='value' or key=value
        for m in re.finditer(r"(\w+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))", text):
            key = m.group(1)
            val = m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None else (m.group(4) or ''))
            attrs[key] = val
        return attrs

    def _strip_comments_and_scripts(self, content: str) -> str:
        """JSP/HTMLのコメントと<script>ブロックを取り除いた文字列を返す（抽出用のクリーン版）。"""
        s = re.sub(r'<%--.*?--%>', '', content, flags=re.DOTALL)
        s = re.sub(r'<!--.*?-->', '', s, flags=re.DOTALL)
        s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.DOTALL | re.IGNORECASE)
        return s

    def _remove_java_string_literals(self, code: str) -> str:
        """Java/C 形式の文字列リテラルと文字リテラルを除去し、キーワード検出時の誤検出を防ぎます。"""
        # ダブルクォート/シングルクォートの文字列と文字リテラルを簡易的に置換
        code = re.sub(r'"(\\.|[^"\\])*"', '""', code)
        code = re.sub(r"'(\\.|[^'\\])*'", "''", code)
        # ブロックコメントと行コメントを除去
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        return code

    def _resolve_tag_file(self, prefix: str, tagname: str, caller_file_id: str) -> Optional[str]:
        """カスタムタグ(prefix:tagname)を既知の .tag/.tagx ファイルIDに解決しようとします。
        見つかれば target_id を返し、見つからなければ None を返します。
        戦略:
          1) プロジェクト内で basename(tagname.tag/.tagx) を探す
          2) 呼び出し元の tag_libraries 宣言を参照して prefix->uri をマップし、その uri 配下を検索する
          3) WEB-INF/tags 配下のタグファイルを優先する
        """
        candidates = [f"{tagname}.tag", f"{tagname}.tagx", tagname]

        # WEB-INF/tags 配下を優先
        for target_id, info in self.jsp_files.items():
            p = info.get('path','')
            base = os.path.basename(p)
            if base in candidates and '/WEB-INF/tags/' in p:
                return target_id

        # プロジェクト内のベース名マッチを検索
        for target_id, info in self.jsp_files.items():
            p = info.get('path','')
            base = os.path.basename(p)
            if base in candidates:
                return target_id

        # 呼び出し元の taglib 宣言を参照して解決を試みる
        if caller_file_id in self.tag_libraries:
            for lib in self.tag_libraries[caller_file_id]:
                uri = lib.get('uri','')
                if uri:
                    candidate_suffix = uri.split(':')[-1].lstrip('/')
                    for target_id, info in self.jsp_files.items():
                        p = info.get('path','')
                        if p.endswith(os.path.join(candidate_suffix, f"{tagname}.tag")) or p.endswith(os.path.join(candidate_suffix, f"{tagname}.tagx")):
                            return target_id

        return None

    def _extract_directives(self, content, file_id):
        """JSPディレクティブを抽出"""
        patterns = {
            'page': r'<%@\s*page\s+([^%>]+)%>',
            'include': r'<%@\s*include\s+([^%>]+)%>',
            'taglib': r'<%@\s*taglib\s+([^%>]+)%>',
            'tag': r'<%@\s*tag\s+([^%>]+)%>',
            'attribute': r'<%@\s*attribute\s+([^%>]+)%>',
            'variable': r'<%@\s*variable\s+([^%>]+)%>'
        }
        
        for directive_type, pattern in patterns.items():
            for match in re.finditer(pattern, content, re.DOTALL):
                directive_content = match.group(1)
                
                attributes = {}
                for attr_match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']+)["\']', directive_content):
                    attributes[attr_match.group(1)] = attr_match.group(2)
                
                self.directives[file_id].append({
                    'type': directive_type,
                    'attributes': attributes,
                    'raw': match.group(0)
                })
                
                # タグライブラリの場合は別途記録
                if directive_type == 'taglib' and 'uri' in attributes and 'prefix' in attributes:
                    self.tag_libraries[file_id].append({
                        'prefix': attributes['prefix'],
                        'uri': attributes['uri']
                    })

    def _extract_includes(self, content, file_id):
        """インクルード関係を抽出"""
        # ディレクティブインクルード
        for match in re.finditer(r'<%@\s*include\s+file\s*=\s*["\']([^"\']+)["\'][^%>]*%>', content):
            self.includes[file_id].append({
                'type': 'directive',
                'file': match.group(1),
                'raw': match.group(0)
            })
        
        # JSPアクションインクルード
        for match in re.finditer(r'<jsp:include\s+[^>]*page\s*=\s*["\']([^"\']+)["\'][^>]*>', content):
            self.includes[file_id].append({
                'type': 'action',
                'page': match.group(1),
                'raw': match.group(0)
            })
        
        # JSTL c:import
        for match in re.finditer(r'<c:import\s+[^>]*url\s*=\s*["\']([^"\']+)["\'][^>]*>', content):
            self.includes[file_id].append({
                'type': 'c:import',
                'url': match.group(1),
                'raw': match.group(0)
            })

    def _extract_scriptlets(self, content, file_id):
        """スクリプトレットを抽出"""
        clean = self._strip_comments_and_scripts(content)

        # _extract_includes ですでにインクルード抽出を行っているが、冗長性のためここでもディレクティブ形式を補足する
        for match in re.finditer(r'<%@\s*include\s+([^%>]+)%>', clean, flags=re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            f = attrs.get('file') or attrs.get('page')
            if f:
                self.includes[file_id].append({
                    'type': 'directive',
                    'file': f,
                    'raw': match.group(0)
                })

        # JSPアクションによるインクルード <jsp:include ...>
        for match in re.finditer(r'<jsp:include\s+([^>]+)>', clean, flags=re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            page = attrs.get('page') or attrs.get('file')
            if page:
                self.includes[file_id].append({
                    'type': 'action',
                    'page': page,
                    'raw': match.group(0)
                })

        # JSTL の c:import を抽出
        for match in re.finditer(r'<c:import\s+([^>]+)>', clean, flags=re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            url = attrs.get('url') or attrs.get('page')
            if url:
                self.includes[file_id].append({
                    'type': 'c:import',
                    'url': url,
                    'raw': match.group(0)
                })

        # <% ... %> のスクリプトレットを抽出（ディレクティブ <%@、式 <%=、宣言 <%! は除外）
        for match in re.finditer(r'<%(?!@|=|!)(.*?)%>', content, flags=re.DOTALL):
            code = match.group(1).strip()
            if not code:
                continue
            # 文字列リテラルやコメントを除去してキーワードの誤検出を防止
            clean_code = self._remove_java_string_literals(code)
            # 行数と改良された複雑度ヒューリスティックを計算
            lines = len(code.splitlines())

            # ASTベース解析を javalang が利用可能な場合に試行
            decision_count = 0
            logical_ops = 0
            ternary_ops = 0
            nesting_score = 0

            if HAS_JAVALANG:
                try:
                    # javalang はコンパイルユニットを期待するため、必要に応じてダミークラス/メソッドでラップする
                    wrapped = f"class X {{ void m() {{ {clean_code} }} }}"
                    tree = javalang.parse.parse(wrapped)

                    # AST を辿って分岐ノードをカウントし、ネストを推定する
                    max_depth = 0
                    cur_depth = 0

                    for path, node in tree:
                        nodename = type(node).__name__
                        # 分岐やループ系ノードを発見したらカウント
                        if nodename in ('IfStatement', 'ForStatement', 'WhileStatement', 'DoStatement', 'SwitchStatement', 'TryStatement'):
                            decision_count += 1
                        # 三項演算子をカウント
                        if nodename == 'TernaryExpression' or nodename == 'ConditionalExpression':
                            ternary_ops += 1
                        # BinaryOperation ノードの演算子が && または || の場合は論理演算子としてカウント
                        if nodename == 'BinaryOperation':
                            op = getattr(node, 'operator', None)
                            if op in ['&&', '||']:
                                logical_ops += 1

                        # BlockStatement / Block ノードでネストを近似
                        if nodename in ('BlockStatement', 'Block'):
                            cur_depth += 1
                            if cur_depth > max_depth:
                                max_depth = cur_depth
                        # ブロックを抜けるようなノードで深さを軽減する（完全ではないがヒューリスティック）
                        if nodename in ('ReturnStatement', 'BreakStatement', 'ContinueStatement'):
                            cur_depth = max(0, cur_depth - 1)

                    nesting_score = int(max_depth / 2)
                except Exception:
                    # パースに失敗した場合は従来のヒューリスティックにフォールバック
                    decision_keywords = [r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bswitch\b', r'\bcase\b', r'\bcatch\b', r'\belse\b']
                    decision_count = sum(len(re.findall(kw, clean_code, flags=re.IGNORECASE)) for kw in decision_keywords)
                    logical_ops = len(re.findall(r'&&|\|\|', clean_code))
                    ternary_ops = len(re.findall(r'\?', clean_code))
                    max_depth = 0
                    cur_depth = 0
                    for ch in clean_code:
                        if ch == '{':
                            cur_depth += 1
                            if cur_depth > max_depth:
                                max_depth = cur_depth
                        elif ch == '}':
                            cur_depth = max(0, cur_depth - 1)
                    nesting_score = int(max_depth / 2)
            else:
                # javalang が利用できない場合は従来のヒューリスティックを使用
                decision_keywords = [r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bswitch\b', r'\bcase\b', r'\bcatch\b', r'\belse\b']
                decision_count = sum(len(re.findall(kw, clean_code, flags=re.IGNORECASE)) for kw in decision_keywords)
                logical_ops = len(re.findall(r'&&|\|\|', clean_code))
                ternary_ops = len(re.findall(r'\?', clean_code))
                max_depth = 0
                cur_depth = 0
                for ch in clean_code:
                    if ch == '{':
                        cur_depth += 1
                        if cur_depth > max_depth:
                            max_depth = cur_depth
                    elif ch == '}':
                        cur_depth = max(0, cur_depth - 1)
                nesting_score = int(max_depth / 2)

            complexity = decision_count + logical_ops + ternary_ops + nesting_score
            if complexity <= 0:
                complexity = 1

            self.scriptlets[file_id].append({
                'code': code,
                'clean_code': clean_code,
                'lines': lines,
                'complexity': complexity,
                'start_position': match.start(),
                'raw': match.group(0)
            })

    def _extract_expressions(self, content, file_id):
        """JSP式を抽出"""
        expression_pattern = r'<%=(.*?)%>'
        for match in re.finditer(expression_pattern, content, re.DOTALL):
            expression = match.group(1).strip()
            self.expressions[file_id].append({
                'expression': expression,
                'start_position': match.start(),
                'raw': match.group(0)
            })

    def _extract_declarations(self, content, file_id):
        """JSP宣言を抽出"""
        declaration_pattern = r'<%!(.*?)%>'
        for match in re.finditer(declaration_pattern, content, re.DOTALL):
            declaration = match.group(1).strip()
            self.declarations[file_id].append({
                'declaration': declaration,
                'start_position': match.start(),
                'raw': match.group(0)
            })

    def _extract_actions(self, content, file_id):
        """JSPアクションを抽出"""
        action_patterns = [
            ('useBean', r'<jsp:useBean\s+([^/>]+)(?:/?>)'),
            ('setProperty', r'<jsp:setProperty\s+([^/>]+)(?:/?>)'),
            ('getProperty', r'<jsp:getProperty\s+([^/>]+)(?:/?>)'),
            ('forward', r'<jsp:forward\s+([^/>]+)(?:/?>)'),
            ('param', r'<jsp:param\s+([^/>]+)(?:/?>)')
        ]
        
        for action_type, pattern in action_patterns:
            for match in re.finditer(pattern, content):
                action_content = match.group(1)
                
                attributes = {}
                for attr_match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']+)["\']', action_content):
                    attributes[attr_match.group(1)] = attr_match.group(2)
                
                self.actions[file_id].append({
                    'type': action_type,
                    'attributes': attributes,
                    'raw': match.group(0)
                })

    def _extract_el_expressions(self, content, file_id):
        """EL式を抽出"""
        # 標準EL式
        for match in re.finditer(r'\${([^}]+)}', content):
            self.el_expressions[file_id].append({
                'expression': match.group(1),
                'type': 'standard',
                'raw': match.group(0)
            })
        
        # 遅延評価EL式
        for match in re.finditer(r'#{([^}]+)}', content):
            self.el_expressions[file_id].append({
                'expression': match.group(1),
                'type': 'deferred',
                'raw': match.group(0)
            })

    def _extract_jstl_usage(self, content, file_id):
        """JSTL使用状況を抽出"""
        jstl_patterns = {
            'core': r'<c:(\w+)',
            'fmt': r'<fmt:(\w+)',
            'sql': r'<sql:(\w+)',
            'xml': r'<x:(\w+)',
            'fn': r'fn:(\w+)\('
        }
        
        for tag_type, pattern in jstl_patterns.items():
            for match in re.finditer(pattern, content):
                tag_name = match.group(1)
                self.jstl_usage[file_id].append({
                    'library': tag_type,
                    'tag': tag_name,
                    'raw': match.group(0)
                })

    def _extract_custom_tags(self, content, file_id):
        """カスタムタグを抽出"""
        custom_tag_pattern = r'<([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)'
        for match in re.finditer(custom_tag_pattern, content):
            prefix = match.group(1)
            tag = match.group(2)
            
            # JSTL標準タグは除外
            if prefix not in ['c', 'fmt', 'sql', 'x', 'fn', 'jsp']:
                self.custom_tags[file_id].append({
                    'prefix': prefix,
                    'tag': tag,
                    'raw': match.group(0)
                })

    def _extract_forms(self, content, file_id):
        """フォーム情報を抽出"""
        clean = self._strip_comments_and_scripts(content)

        if HAS_BEAUTIFULSOUP:
            try:
                soup = BeautifulSoup(clean, 'html.parser')
                for form in soup.find_all('form'):
                    action = form.get('action') or ''
                    method = (form.get('method') or 'get').lower()
                    inputs = form.find_all(['input', 'select', 'textarea'])
                    form_info = {
                        'action': action,
                        'method': method,
                        'inputs': [i.name for i in inputs],
                        'input_count': sum(1 for i in inputs if i.name == 'input'),
                        'select_count': sum(1 for i in inputs if i.name == 'select'),
                        'textarea_count': sum(1 for i in inputs if i.name == 'textarea')
                    }
                    self.forms[file_id].append(form_info)
                return
            except Exception:
                pass

        # fallback: regex-based extraction
        form_pattern = r'<form\s+([^>]+)>(.*?)</form>'
        for match in re.finditer(form_pattern, clean, re.DOTALL | re.IGNORECASE):
            form_attrs = match.group(1)
            form_content = match.group(2)
            attrs = self._parse_attributes(form_attrs)
            form_info = {
                'action': attrs.get('action', ''),
                'method': attrs.get('method', 'get').lower(),
                'inputs': [],
                'input_count': len(re.findall(r'<input\s+', form_content, flags=re.IGNORECASE)),
                'select_count': len(re.findall(r'<select\s+', form_content, flags=re.IGNORECASE)),
                'textarea_count': len(re.findall(r'<textarea\s+', form_content, flags=re.IGNORECASE))
            }
            self.forms[file_id].append(form_info)

    def _extract_implicit_objects(self, content, file_id):
        """暗黙オブジェクトの使用を抽出"""
        # セッション使用
        session_patterns = [
            r'session\.getAttribute\(["\'](\w+)["\']\)',
            r'session\.setAttribute\(["\'](\w+)["\']',
            r'session\.removeAttribute\(["\'](\w+)["\']\)',
            r'\${sessionScope\.(\w+)}'
        ]
        
        for pattern in session_patterns:
            for match in re.finditer(pattern, content):
                operation = 'get' if 'getAttribute' in pattern or 'sessionScope' in pattern else 'set' if 'setAttribute' in pattern else 'remove'
                self.session_usage[file_id].append({
                    'attribute': match.group(1) if match.lastindex else 'unknown',
                    'operation': operation,
                    'raw': match.group(0)
                })
        
        # リクエスト使用
        request_patterns = [
            r'request\.getParameter\(["\'](\w+)["\']\)',
            r'request\.getAttribute\(["\'](\w+)["\']\)',
            r'request\.setAttribute\(["\'](\w+)["\']',
            r'\${param\.(\w+)}'
        ]
        
        for pattern in request_patterns:
            for match in re.finditer(pattern, content):
                operation = 'parameter' if 'getParameter' in pattern or 'param.' in pattern else 'get' if 'getAttribute' in pattern else 'set'
                self.request_usage[file_id].append({
                    'attribute': match.group(1) if match.lastindex else 'unknown',
                    'operation': operation,
                    'raw': match.group(0)
                })
        
        # レスポンス使用
        response_patterns = [
            r'response\.sendRedirect\(["\']([^"\']+)["\']\)',
            r'response\.setContentType\(["\']([^"\']+)["\']\)'
        ]
        
        for pattern in response_patterns:
            for match in re.finditer(pattern, content):
                operation = 'redirect' if 'sendRedirect' in pattern else 'content_type'
                self.response_usage[file_id].append({
                    'operation': operation,
                    'value': match.group(1) if match.lastindex else '',
                    'raw': match.group(0)
                })

    def _extract_db_operations(self, content, file_id):
        """データベース操作を抽出"""
        # JDBC接続パターン
        connection_patterns = [
            r'Connection\s+\w+\s*=',
            r'DriverManager\.getConnection',
            r'DataSource\s+\w+\s*='
        ]
        
        for pattern in connection_patterns:
            if re.search(pattern, content):
                self.db_operations[file_id].append({
                    'type': 'connection',
                    'pattern': pattern
                })
        
        # SQL実行パターン
        sql_patterns = [
            r'executeQuery\(["\']([^"\']+)["\']\)',
            r'executeUpdate\(["\']([^"\']+)["\']\)',
            r'prepareStatement\(["\']([^"\']+)["\']\)'
        ]
        
        for pattern in sql_patterns:
            for match in re.finditer(pattern, content):
                sql = match.group(1)
                operation_type = 'query' if 'select' in sql.lower() else 'update'
                
                self.db_operations[file_id].append({
                    'type': 'sql',
                    'sql': sql,
                    'operation': operation_type
                })

    def _extract_frontend_elements(self, content, file_id):
        """フロントエンド要素を抽出"""
        # CSSクラス
        for match in re.finditer(r'class\s*=\s*["\']([^"\']+)["\']', content):
            classes = match.group(1).split()
            for css_class in classes:
                if css_class and not css_class.startswith('${'):
                    self.css_classes[file_id].add(css_class)
        
        # JavaScript関数
        for match in re.finditer(r'function\s+(\w+)\s*\(', content):
            self.js_functions[file_id].add(f"def:{match.group(1)}")
        
        for match in re.finditer(r'(\w+)\s*\([^)]*\)', content):
            func_name = match.group(1)
            if func_name not in ['if', 'for', 'while', 'switch', 'catch']:
                self.js_functions[file_id].add(f"call:{func_name}")

    def _calculate_file_metrics(self, content, file_id):
        """ファイルメトリクスを計算"""
        metrics = {
            'ファイルパス': self.jsp_files[file_id]['path'],
            'コード行数': len(content.split('\n')),
            'ファイルサイズ': self.jsp_files[file_id]['size'],
            
            # ディレクティブ
            'ページディレクティブ数': sum(1 for d in self.directives[file_id] if d['type'] == 'page'),
            'インクルードディレクティブ数': sum(1 for d in self.directives[file_id] if d['type'] == 'include'),
            'タグライブラリディレクティブ数': sum(1 for d in self.directives[file_id] if d['type'] == 'taglib'),
            '合計ディレクティブ数': len(self.directives[file_id]),
            
            # スクリプトレット
            'スクリプトレット数': len(self.scriptlets[file_id]),
            'スクリプトレット行数': sum(s['lines'] for s in self.scriptlets[file_id]),
            '式（Expression）数': len(self.expressions[file_id]),
            '宣言スクリプトレット数': len(self.declarations[file_id]),
            
            # タグ使用
            'JSTL合計タグ数': len(self.jstl_usage[file_id]),
            'JSTLコアタグ数': sum(1 for j in self.jstl_usage[file_id] if j['library'] == 'core'),
            'JSTL書式タグ数': sum(1 for j in self.jstl_usage[file_id] if j['library'] == 'fmt'),
            'カスタムタグ数': len(self.custom_tags[file_id]),
            
            # EL式
            'EL式合計': len(self.el_expressions[file_id]),
            '標準EL式数': sum(1 for e in self.el_expressions[file_id] if e['type'] == 'standard'),
            '遅延評価EL式数': sum(1 for e in self.el_expressions[file_id] if e['type'] == 'deferred'),
            
            # HTML要素
            'HTML要素数': len(re.findall(r'<[a-zA-Z][^>]*>', content)),
            'フォーム数': len(self.forms[file_id]),
            '入力要素数': sum(f['input_count'] + f['select_count'] + f['textarea_count'] for f in self.forms[file_id]),
            
            # JavaScript/CSS
            'JavaScript ブロック数': len(re.findall(r'<script[^>]*>', content)),
            'CSS ブロック数': len(re.findall(r'<style[^>]*>', content)),
            'CSSクラス数': len(self.css_classes[file_id]),
            
            # インクルード
            '合計インクルード数': len(self.includes[file_id]),
            'インクルードディレクティブ数': sum(1 for i in self.includes[file_id] if i['type'] == 'directive'),
            'インクルードアクション数': sum(1 for i in self.includes[file_id] if i['type'] == 'action'),
            
            # コメント
            'HTMLコメント数': len(re.findall(r'<!--.*?-->', content, re.DOTALL)),
            'JSPコメント数': len(re.findall(r'<%--.*?--%>', content, re.DOTALL)),
            
            # 暗黙オブジェクト使用
            'セッション使用数': len(self.session_usage[file_id]),
            'リクエスト使用数': len(self.request_usage[file_id]),
            'レスポンス使用数': len(self.response_usage[file_id]),
            
            # DB操作
            'DB操作数': len(self.db_operations[file_id]),
            
            # セキュリティ問題
            'セキュリティ問題合計': len(self.security_issues[file_id])
        }
        
        # ASTベースのスクリプトレット複雑度を集計（存在すればより精緻）
        ast_scriptlet_complexity = sum(s.get('complexity', 0) for s in self.scriptlets[file_id])
        metrics['ASTスクリプトレット複雑度'] = ast_scriptlet_complexity

        # 循環的複雑度を計算（基本1 + AST複雑度）
        complexity = 1 + ast_scriptlet_complexity

        # JSTL条件タグも複雑度に加算
        complexity += sum(1 for j in self.jstl_usage[file_id] if j['tag'] in ['if', 'when', 'choose', 'forEach'])

        metrics['循環的複雑度'] = complexity

        # JSP複雑度指標を計算
        # JSP 複雑度指標: ASTスクリプトレット複雑度を主要因として使用
        jsp_complexity = (
            ast_scriptlet_complexity * 0.3 +
            metrics['スクリプトレット数'] * 0.15 +
            metrics['EL式合計'] * 0.05 +
            metrics['JSTL合計タグ数'] * 0.05 +
            metrics['カスタムタグ数'] * 0.05 +
            metrics['HTML要素数'] * 0.001 +
            metrics['JavaScript ブロック数'] * 0.1 +
            complexity * 0.15 +
            metrics['セキュリティ問題合計'] * 0.15
        )
        metrics['JSP複雑度指標'] = round(jsp_complexity, 2)

        self.metrics[file_id] = metrics

    def _detect_security_issues(self, content, file_id):
        """セキュリティ問題を検出"""
        # SQLインジェクション脆弱性
        sql_injection_patterns = [
            r'Statement\.execute\([^)]*\+',
            r'executeQuery\([^)]*\+',
            r'executeUpdate\([^)]*\+'
        ]
        
        for pattern in sql_injection_patterns:
            for match in re.finditer(pattern, content):
                self.security_issues[file_id].append({
                    'type': 'sql_injection',
                    'pattern': match.group(0),
                    'message': 'SQLインジェクションの危険性があります'
                })
        
        # XSS脆弱性
        xss_patterns = [
            r'<%=\s*request\.getParameter\(["\'][^"\']*["\']',
            r'out\.print\(\s*request\.getParameter'
        ]
        
        for pattern in xss_patterns:
            for match in re.finditer(pattern, content):
                self.security_issues[file_id].append({
                    'type': 'xss',
                    'pattern': match.group(0),
                    'message': 'XSS脆弱性の危険性があります'
                })

    def build_dependency_graph(self):
        """依存関係グラフを構築"""
        # グラフにノードを追加
        for file_id in self.jsp_files.keys():
            self.dependency_graph.add_node(file_id)
        
        # インクルードによる依存関係
        for file_id, includes in self.includes.items():
            for include in includes:
                if include['type'] == 'directive':
                    target = include.get('file', '')
                elif include['type'] == 'action':
                    target = include.get('page', '')
                elif include['type'] == 'c:import':
                    target = include.get('url', '')
                else:
                    continue
                
                if target:
                    raw_target = target
                    # skip dynamic targets containing EL or scriptlets
                    if '${' in raw_target or '<%' in raw_target:
                        # record dynamic include for traceability
                        self.dependencies[file_id].append({
                            'target': None,
                            'type': include['type'],
                            'dynamic': True,
                            'raw': raw_target
                        })
                        continue

                    # strip query params
                    target_no_query = raw_target.split('?', 1)[0]

                    # normalize separators
                    normalized_target = os.path.normpath(target_no_query).replace('\\', '/')

                    # build candidate paths to match against known files
                    candidates = set()
                    candidates.add(normalized_target)
                    candidates.add(normalized_target.lstrip('/'))
                    candidates.add(os.path.basename(normalized_target))

                    # if relative path, resolve against caller directory
                    caller_info = self.jsp_files.get(file_id, {})
                    caller_path = caller_info.get('path', '')
                    if caller_path and not normalized_target.startswith('/'):
                        caller_dir = os.path.dirname(caller_path)
                        resolved = os.path.normpath(os.path.join(caller_dir, normalized_target)).replace('\\', '/')
                        candidates.add(resolved)

                    matched = False
                    for target_id, target_info in self.jsp_files.items():
                        target_path = target_info.get('path', '')
                        if not target_path:
                            continue

                        # normalized target path variants for comparison
                        tpath_norm = target_path.replace('\\', '/')
                        tpath_norm_strip = tpath_norm.lstrip('/')

                        # check direct contains/endswith matches
                        if any(tpath_norm.endswith(cand) or cand.endswith(tpath_norm) or tpath_norm_strip.endswith(cand) or os.path.basename(tpath_norm) == cand for cand in candidates):
                            self.dependency_graph.add_edge(file_id, target_id)
                            self.dependencies[file_id].append({
                                'target': target_id,
                                'type': include['type'],
                                'raw': raw_target
                            })
                            matched = True
                            break

                    if not matched:
                        # no exact match found; try basename fallback search
                        bt = os.path.basename(normalized_target)
                        for target_id, target_info in self.jsp_files.items():
                            if os.path.basename(target_info.get('path', '')) == bt:
                                self.dependency_graph.add_edge(file_id, target_id)
                                self.dependencies[file_id].append({
                                    'target': target_id,
                                    'type': include['type'],
                                    'raw': raw_target,
                                    'note': 'basename_fallback'
                                })
                                matched = True
                                break
        
        # フォームアクションによる依存関係
        for file_id, forms in self.forms.items():
            for form in forms:
                action = form.get('action', '')
                if action and not action.startswith(('javascript:', 'http:', 'https:')):
                    normalized_action = os.path.normpath(action).replace('\\', '/')
                    
                    for target_id, target_info in self.jsp_files.items():
                        if target_info['path'].endswith(normalized_action):
                            self.dependency_graph.add_edge(file_id, target_id)
                            self.dependencies[file_id].append({
                                'target': target_id,
                                'type': 'form_action'
                            })
                            break

        # カスタムタグ使用による依存関係（タグファイル .tag/.tagx を推測してマッチ）
        for file_id, tags in self.custom_tags.items():
            for tag_usage in tags:
                prefix = tag_usage.get('prefix')
                tagname = tag_usage.get('tag')

                # try to resolve via helper _resolve_tag_file which consolidates multiple heuristics
                target_id = self._resolve_tag_file(prefix, tagname, caller_file_id=file_id)
                if target_id:
                    self.dependency_graph.add_edge(file_id, target_id)
                    self.dependencies[file_id].append({
                        'target': target_id,
                        'type': 'custom_tag',
                        'tag_prefix': prefix,
                        'tag_name': tagname,
                        'raw': tag_usage.get('raw')
                    })
                    continue
                # if still not resolved, fallback to basename scan
                candidates = [f"{tagname}.tag", f"{tagname}.tagx", tagname]
                for target_id, target_info in self.jsp_files.items():
                    tpath = target_info.get('path', '')
                    if not tpath:
                        continue
                    base = os.path.basename(tpath)
                    if base in candidates:
                        self.dependency_graph.add_edge(file_id, target_id)
                        self.dependencies[file_id].append({
                            'target': target_id,
                            'type': 'custom_tag_fallback',
                            'tag_prefix': prefix,
                            'tag_name': tagname,
                            'raw': tag_usage.get('raw')
                        })
                        break

    def calculate_coupling_metrics(self):
        """結合度メトリクスを計算"""
        for node in self.dependency_graph.nodes():
            in_degree = self.dependency_graph.in_degree(node)
            out_degree = self.dependency_graph.out_degree(node)
            total_coupling = in_degree + out_degree
            
            # インスタビリティ
            instability = out_degree / total_coupling if total_coupling > 0 else 0
            
            # 循環的依存関係の検出
            has_cyclic = False
            try:
                cycles = list(nx.simple_cycles(self.dependency_graph))
                has_cyclic = any(node in cycle for cycle in cycles)
            except:
                pass
            
            self.coupling_metrics[node] = {
                '流入結合度': in_degree,
                '流出結合度': out_degree,
                '合計結合度': total_coupling,
                'インスタビリティ': round(instability, 2),
                '循環的依存関係': has_cyclic
            }
            
            # メトリクスに追加
            if node in self.metrics:
                self.metrics[node].update(self.coupling_metrics[node])

    def _analyze_html_patterns(self):
        """HTMLパターンを解析"""
        if not HAS_BEAUTIFULSOUP:
            return
        
        for file_id, file_info in self.jsp_files.items():
            try:
                content = self._read_file_content(file_info['full_path'])
                if not content:
                    continue
                
                # JSP要素を削除
                clean_content = re.sub(r'<%.*?%>', '', content, flags=re.DOTALL)
                clean_content = re.sub(r'\${[^}]+}', '', clean_content)
                clean_content = re.sub(r'<[a-z]+:[^>]+/?>', '', clean_content)
                
                soup = BeautifulSoup(clean_content, 'html.parser')
                
                pattern_info = {
                    'tables': len(soup.find_all('table')),
                    'forms': len(soup.find_all('form')),
                    'divs': len(soup.find_all('div')),
                    'lists': len(soup.find_all(['ul', 'ol'])),
                    'headers': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                    'images': len(soup.find_all('img')),
                    'links': len(soup.find_all('a'))
                }
                
                self.html_patterns[file_id] = pattern_info
                
            except Exception as e:
                self.log(f"警告: {file_id} のHTMLパターン解析中にエラー: {e}")

    def _analyze_java_patterns(self):
        """Javaパターンを解析"""
        for file_id, scriptlets in self.scriptlets.items():
            if not scriptlets:
                continue
            
            pattern_info = {
                'loop_patterns': 0,
                'condition_patterns': 0,
                'db_patterns': 0,
                'var_declaration_patterns': 0,
                'complexity': 0
            }
            
            combined_code = '\n'.join([s.get('code', '') for s in scriptlets])
            
            # ループパターン
            pattern_info['loop_patterns'] = (
                len(re.findall(r'\bfor\b', combined_code)) +
                len(re.findall(r'\bwhile\b', combined_code)) +
                len(re.findall(r'\bdo\b', combined_code))
            )
            
            # 条件パターン
            pattern_info['condition_patterns'] = (
                len(re.findall(r'\bif\b', combined_code)) +
                len(re.findall(r'\bswitch\b', combined_code))
            )
            
            # DB操作パターン
            pattern_info['db_patterns'] = (
                len(re.findall(r'Connection\b', combined_code)) +
                len(re.findall(r'Statement\b', combined_code)) +
                len(re.findall(r'ResultSet\b', combined_code))
            )
            
            # 変数宣言パターン
            pattern_info['var_declaration_patterns'] = len(
                re.findall(r'(?:int|String|boolean|long|double|float|List|Map|Set)\s+\w+', combined_code)
            )
            
            # 複雑さスコア
            pattern_info['complexity'] = sum(s.get('complexity', 0) for s in scriptlets)
            
            self.java_patterns[file_id] = pattern_info

    def _identify_issue_patterns(self):
        """問題パターンを検出"""
        for file_id, file_info in self.jsp_files.items():
            # スクリプトレットの過剰使用
            if file_id in self.scriptlets and len(self.scriptlets[file_id]) > 5:
                self.issues[file_id].append({
                    'type': 'excessive_scriptlets',
                    'count': len(self.scriptlets[file_id]),
                    'message': 'スクリプトレットの過剰使用は保守性が低下します'
                })
            
            # 大きすぎるファイル
            if file_info['size'] > 30000:  # 30KB以上
                self.issues[file_id].append({
                    'type': 'large_file',
                    'size': file_info['size'],
                    'message': 'ファイルが大きすぎます。分割を検討してください'
                })
            
            # セキュリティ問題
            if file_id in self.security_issues and self.security_issues[file_id]:
                for issue in self.security_issues[file_id]:
                    self.issues[file_id].append(issue)
            
            # 循環的依存関係
            if file_id in self.coupling_metrics and self.coupling_metrics[file_id].get('循環的依存関係'):
                self.issues[file_id].append({
                    'type': 'cyclic_dependency',
                    'message': '循環的依存関係が検出されました'
                })

    def generate_csv_report(self, output_file):
        """CSV形式でレポートを生成"""
        if not self.metrics:
            print("書き込むメトリクスがありません")
            return
        
        # フィールド名を収集
        all_fields = set()
        for metrics in self.metrics.values():
            all_fields.update(metrics.keys())
        
        # 重要なフィールドを先頭に配置
        priority_fields = [
            'ファイルパス', 'コード行数', '循環的複雑度', 'JSP複雑度指標',
            'スクリプトレット数', 'EL式合計', 'JSTL合計タグ数',
            'セキュリティ問題合計', '流入結合度', '流出結合度', 'クラスタ'
        ]
        
        fieldnames = [f for f in priority_fields if f in all_fields]
        fieldnames.extend(sorted(f for f in all_fields if f not in priority_fields))
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            # ensure each row includes cluster info if present
            for m in self.metrics.values():
                row = {k: m.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        print(f"CSVレポートを {output_file} に保存しました")

    def compute_clusters_and_plot(self, output_dir):
        """複雑度（JSP複雑度指標）と行数で3x3のクラスタに分類しプロットを出力します。
        クラスタは行数と複雑度をそれぞれ tertile（3分位）でビニングして 3x3 の組合せで識別します。
        """
        if not self.metrics:
            print('メトリクスが空のためクラスタリングをスキップします')
            return

        x = []  # 行数
        y = []  # 複雑度
        ids = []
        for file_id, m in self.metrics.items():
            ids.append(file_id)
            x.append(m.get('コード行数', 0))
            y.append(m.get('JSP複雑度指標', 0.0))

        x = np.array(x)
        y = np.array(y)

        # tertile の閾値を計算（要素数が少ない場合は最大値を閾値として扱う）
        x_thresh = np.percentile(x, [33.33, 66.66]) if len(x) > 2 else (np.max(x), np.max(x))
        y_thresh = np.percentile(y, [33.33, 66.66]) if len(y) > 2 else (np.max(y), np.max(y))

        clusters = {}
        for i, file_id in enumerate(ids):
            xi = x[i]
            yi = y[i]
            # それぞれ 0,1,2 のインデックスにマップ
            cx = 0 if xi <= x_thresh[0] else (1 if xi <= x_thresh[1] else 2)
            cy = 0 if yi <= y_thresh[0] else (1 if yi <= y_thresh[1] else 2)
            cluster_id = cy * 3 + cx  # 0..8
            clusters[file_id] = cluster_id
            # メトリクスに追記
            self.metrics[file_id]['クラスタ'] = int(cluster_id)
            # クラスタ種類（説明ラベル）を追加
            complexity_labels = ['低', '中', '高']
            size_labels = ['小', '中', '大']
            label_body = f"{complexity_labels[cy]}複雑度・{size_labels[cx]}規模"
            # ソート可能な2桁接頭辞 (01..09) を付与
            num_prefix = f"{int(cluster_id)+1:02d}"
            cluster_label = f"{num_prefix} - {label_body}"
            self.metrics[file_id]['クラスタ種類'] = cluster_label

        # プロット用データ（ゼロを避けるために +1 を用いる）
        x_pos = x + 1
        y_pos = y + 1

        plt.figure(figsize=(8,6))

        # hexbin による密度背景（対数ビン）
        hb = plt.hexbin(x_pos, y_pos, gridsize=40, bins='log', cmap='Greys', mincnt=1)
        cb = plt.colorbar(hb)
        cb.set_label('log10(count)')

        # クラスタ点を重ねる
        cmap = plt.get_cmap('tab10')
        colors = [cmap(i) for i in range(9)]
        for c in range(9):
            idxs = [i for i, fid in enumerate(ids) if clusters[fid] == c]
            if not idxs:
                continue
            plt.scatter(x_pos[idxs], y_pos[idxs], c=[colors[c]], s=30, alpha=0.9, label=f'Cluster {c}', edgecolors='none')

        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Lines of code (log scale)')
        plt.ylabel('JSP complexity score (log scale)')
        plt.title('JSP: Lines vs Complexity (3x3 clusters)')

        # tertile のラインを描画（元のスケールに合わせて +1）
        for xt in x_thresh:
            plt.axvline(xt+1, color='grey', linestyle='--', linewidth=0.8)
        for yt in y_thresh:
            plt.axhline(yt+1, color='grey', linestyle='--', linewidth=0.8)

        # ラベルが無い場合の警告は無視
        try:
            plt.legend(ncol=3, fontsize='small')
        except Exception:
            pass

        # 固定ファイル名で出力
        out_png = os.path.join(output_dir, 'jsp_clusters.png')
        plt.tight_layout()
        plt.savefig(out_png)
        plt.close()

        print(f"Cluster plot saved to {out_png}")

    def generate_markdown_report(self, output_file):
        """Markdown形式でレポートを生成"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # ヘッダー
            f.write('# JSPファイル解析レポート\n\n')
            f.write(f'**プロジェクト**: {os.path.basename(self.project_dir)}\n')
            f.write(f'**解析日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'**JSPファイル数**: {len(self.jsp_files)}\n\n')
            
            # サマリー統計
            f.write('## サマリー統計\n\n')
            
            if self.metrics:
                total_loc = sum(m.get('コード行数', 0) for m in self.metrics.values())
                total_scriptlets = sum(m.get('スクリプトレット数', 0) for m in self.metrics.values())
                total_jstl = sum(m.get('JSTL合計タグ数', 0) for m in self.metrics.values())
                total_el = sum(m.get('EL式合計', 0) for m in self.metrics.values())
                
                f.write(f'- **総コード行数**: {total_loc:,}\n')
                f.write(f'- **総スクリプトレット数**: {total_scriptlets:,}\n')
                f.write(f'- **総JSTLタグ数**: {total_jstl:,}\n')
                f.write(f'- **総EL式数**: {total_el:,}\n\n')
            
            # 問題の検出
            if self.issues:
                f.write('## 検出された問題\n\n')
                
                issue_summary = defaultdict(int)
                for issues in self.issues.values():
                    for issue in issues:
                        issue_summary[issue['type']] += 1
                
                f.write('| 問題タイプ | 件数 |\n')
                f.write('|-----------|------|\n')
                for issue_type, count in sorted(issue_summary.items(), key=lambda x: x[1], reverse=True):
                    f.write(f'| {issue_type} | {count} |\n')
                f.write('\n')
            
            # 複雑度の高いファイル
            if self.metrics:
                f.write('## 複雑度の高いファイル（上位10件）\n\n')
                
                sorted_by_complexity = sorted(
                    self.metrics.items(),
                    key=lambda x: x[1].get('JSP複雑度指標', 0),
                    reverse=True
                )[:10]
                
                f.write('| ファイル | JSP複雑度指標 | 循環的複雑度 |\n')
                f.write('|---------|--------------|-------------|\n')
                for file_id, metrics in sorted_by_complexity:
                    file_name = os.path.basename(self.jsp_files[file_id]['path'])
                    complexity = metrics.get('JSP複雑度指標', 0)
                    cyclomatic = metrics.get('循環的複雑度', 0)
                    f.write(f'| {file_name} | {complexity:.2f} | {cyclomatic} |\n')
                f.write('\n')
            
            # 依存関係
            if self.dependencies:
                f.write('## ファイル依存関係\n\n')
                
                # 最も依存されているファイル
                in_degrees = defaultdict(int)
                for deps in self.dependencies.values():
                    for dep in deps:
                        in_degrees[dep['target']] += 1
                
                if in_degrees:
                    f.write('### 最も依存されているファイル（上位5件）\n\n')
                    sorted_deps = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    for file_id, count in sorted_deps:
                        if file_id in self.jsp_files:
                            file_name = os.path.basename(self.jsp_files[file_id]['path'])
                            f.write(f'- {file_name}: {count}件の依存\n')
                    f.write('\n')
            
            # 推奨事項
            f.write('## 推奨事項\n\n')
            
            recommendations = []
            
            # スクリプトレットの多いファイルがある場合
            if any(len(s) > 5 for s in self.scriptlets.values()):
                recommendations.append('- スクリプトレットをJSTLやEL式、サーブレットに移行することを検討してください')
            
            # セキュリティ問題がある場合
            if self.security_issues:
                recommendations.append('- セキュリティ脆弱性が検出されました。SQLインジェクションとXSS対策を実施してください')
            
            # 循環的依存関係がある場合
            if any(m.get('循環的依存関係') for m in self.coupling_metrics.values()):
                recommendations.append('- 循環的依存関係を解消してアーキテクチャを改善してください')
            
            # 大きすぎるファイルがある場合
            if any(f['size'] > 30000 for f in self.jsp_files.values()):
                recommendations.append('- 大きすぎるJSPファイルを複数の小さなファイルに分割してください')
            
            if recommendations:
                for rec in recommendations:
                    f.write(f'{rec}\n')
            else:
                f.write('- 重大な問題は検出されませんでした\n')
            
            f.write('\n')
        
        print(f"Markdownレポートを {output_file} に保存しました")

    def generate_json_report(self, output_file):
        """JSON形式でレポートを生成"""
        report = {
            'project': os.path.basename(self.project_dir),
            'analysis_date': datetime.now().isoformat(),
            'summary': {
                'total_files': len(self.jsp_files),
                'total_loc': sum(m.get('コード行数', 0) for m in self.metrics.values()),
                'total_issues': sum(len(issues) for issues in self.issues.values())
            },
            'files': {},
            'dependency_graph': {
                'nodes': list(self.dependency_graph.nodes()),
                'edges': list(self.dependency_graph.edges())
            }
        }
        
        # ファイルごとの詳細情報
        for file_id, file_info in self.jsp_files.items():
            report['files'][file_id] = {
                'info': file_info,
                'metrics': self.metrics.get(file_id, {}),
                'issues': self.issues.get(file_id, []),
                'dependencies': self.dependencies.get(file_id, [])
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"JSONレポートを {output_file} に保存しました")

    def generate_jsp_calls_csv(self, output_file):
        """JSP同士の呼び出し関係をCSVで出力"""
        # dependencies: { caller_file_id: [ { 'target': target_id, 'type': type }, ... ] }
        rows = []
        for caller_id, deps in self.dependencies.items():
            caller_path = self.jsp_files.get(caller_id, {}).get('path', caller_id)
            for dep in deps:
                target_id = dep.get('target')
                target_path = self.jsp_files.get(target_id, {}).get('path', target_id)
                rows.append({
                    'caller_id': caller_id,
                    'caller_path': caller_path,
                    'callee_id': target_id,
                    'callee_path': target_path,
                    'relation_type': dep.get('type')
                })

        # write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['caller_id', 'caller_path', 'callee_id', 'callee_path', 'relation_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        print(f"JSP呼び出し関係CSVを {output_file} に保存しました")

    def generate_jsp_calls_markdown(self, output_file):
        """JSP同士の呼び出し関係をMarkdownで出力（呼び出し元ごとに一覧化）"""
        callers = defaultdict(list)
        for caller_id, deps in self.dependencies.items():
            for dep in deps:
                target_id = dep.get('target')
                callers[caller_id].append((target_id, dep.get('type')))

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# JSP 呼び出し関係レポート\n\n')
            f.write(f'生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')

            if not callers:
                f.write('呼び出し関係は検出されませんでした。\n')
                print(f"JSP呼び出し関係Markdownを {output_file} に保存しました")
                return

            for caller_id, targets in sorted(callers.items()):
                caller_path = self.jsp_files.get(caller_id, {}).get('path', caller_id)
                f.write(f'## 呼び出し元: {caller_path}\n\n')
                f.write('| 呼び出し先 | 種別 |\n')
                f.write('|------------|------:|\n')
                for target_id, rel_type in targets:
                    target_path = self.jsp_files.get(target_id, {}).get('path', target_id)
                    f.write(f'| {target_path} | {rel_type} |\n')
                f.write('\n')

        print(f"JSP呼び出し関係Markdownを {output_file} に保存しました")

    def generate_include_usage_csv(self, output_file):
        """共通に使われるインクルードファイルと、それを利用するJSP一覧をCSVで出力"""
        # build mapping: include_target_id -> set(caller_id)
        include_map = defaultdict(set)
        for caller_id, deps in self.dependencies.items():
            for dep in deps:
                target = dep.get('target')
                if target:
                    include_map[target].add(caller_id)

        rows = []
        for target_id, callers in include_map.items():
            target_path = self.jsp_files.get(target_id, {}).get('path', target_id)
            unique_callers = sorted(callers)
            usage_count = len(unique_callers)
            for caller in unique_callers:
                caller_path = self.jsp_files.get(caller, {}).get('path', caller)
                rows.append({
                    'include_id': target_id,
                    'include_path': target_path,
                    'caller_id': caller,
                    'caller_path': caller_path,
                    'usage_count_for_include': usage_count
                })

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['include_id', 'include_path', 'caller_id', 'caller_path', 'usage_count_for_include']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        print(f"Include usage CSV saved to {output_file}")

    def generate_include_usage_markdown(self, output_file):
        """共通に使われるインクルードファイルと、それを利用するJSP一覧をMarkdownで出力"""
        include_map = defaultdict(set)
        for caller_id, deps in self.dependencies.items():
            for dep in deps:
                target = dep.get('target')
                if target:
                    include_map[target].add(caller_id)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# Include Usage Report\n\n')
            f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')

            if not include_map:
                f.write('No include relationships detected.\n')
                print(f"Include usage Markdown saved to {output_file}")
                return

            # usage count の降順でソート
            items = sorted(include_map.items(), key=lambda kv: len(kv[1]), reverse=True)
            for target_id, callers in items:
                target_path = self.jsp_files.get(target_id, {}).get('path', target_id)
                unique_callers = sorted(callers)
                f.write(f'## Include: {target_path} ({len(unique_callers)} usages)\n\n')
                for c in unique_callers:
                    caller_path = self.jsp_files.get(c, {}).get('path', c)
                    f.write(f'- {caller_path}\n')
                f.write('\n')

        print(f"Include usage Markdown saved to {output_file}")

    def generate_include_graph(self, output_file, highlight_common=True):
        """インクルード関係を可視化する有向グラフ（PNG）を生成します。
        highlight_common=True の場合、header/footer/menu/common など共通部と思われるファイルを強調表示します。
        """
        # include -> 呼び出し元集合 のマッピングを構築
        include_map = defaultdict(set)
        for caller_id, deps in self.dependencies.items():
            for dep in deps:
                target = dep.get('target')
                if target:
                    include_map[target].add(caller_id)

        if not include_map:
            print('プロットするインクルード関係がありません')
            return

        G = nx.DiGraph()
        # ノードとエッジを追加して可視化用グラフを作成
        for include_id, callers in include_map.items():
            include_path = self.jsp_files.get(include_id, {}).get('path', include_id)
            G.add_node(include_path, type='include')
            for caller in callers:
                caller_path = self.jsp_files.get(caller, {}).get('path', caller)
                G.add_node(caller_path, type='caller')
                G.add_edge(caller_path, include_path)

        # 共通ファイルとみなす判定
        def is_common(p):
            lp = p.lower()
            return ('/common/' in lp) or any(k in lp for k in ['header', 'footer', 'menu', 'common'])

        # graphviz レイアウトを優先して可読性を確保（利用不可なら spring_layout にフォールバック）
        try:
            pos = None
            try:
                # networkx の pydot バックエンドを優先
                pos = nx.nx_pydot.graphviz_layout(G, prog='dot')
            except Exception:
                # pygraphviz が利用できる場合のフォールバック
                try:
                    pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
                except Exception:
                    pos = None

            if pos is None:
                print('Graphviz レイアウトが利用できないため spring レイアウトにフォールバックします')
                pos = nx.spring_layout(G, seed=42, k=0.5)

        except Exception as e:
            print(f'Graphviz レイアウトエラー: {e}. spring レイアウトを使用します')
            pos = nx.spring_layout(G, seed=42, k=0.5)

        node_colors = []
        node_sizes = []
        labels = {}
        for n, d in G.nodes(data=True):
            # 表示ラベルはファイル名（basename）
            labels[n] = os.path.basename(n)
            if d.get('type') == 'include':
                if highlight_common and is_common(n):
                    node_colors.append('orange')
                    node_sizes.append(800)
                else:
                    node_colors.append('red')
                    node_sizes.append(500)
            else:
                node_colors.append('skyblue')
                node_sizes.append(300)

        plt.figure(figsize=(12, 10))
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
        nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='->', arrowsize=10, edge_color='gray')
        nx.draw_networkx_labels(G, pos, labels, font_size=8)

        plt.title('Include Usage Graph')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()

        print(f'Include graph saved to {output_file}')

    def generate_summary_text(self, output_file):
        """テキスト形式のサマリーレポートを生成"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("JSPプロジェクト解析サマリー\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"プロジェクト: {os.path.basename(self.project_dir)}\n")
            f.write(f"解析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"解析ファイル数: {len(self.jsp_files)}\n\n")
            
            # 基本統計
            if self.metrics:
                f.write("【基本統計】\n")
                f.write(f"総コード行数: {sum(m.get('コード行数', 0) for m in self.metrics.values()):,}\n")
                f.write(f"平均コード行数: {sum(m.get('コード行数', 0) for m in self.metrics.values()) // len(self.metrics)}\n")
                f.write(f"総スクリプトレット数: {sum(m.get('スクリプトレット数', 0) for m in self.metrics.values())}\n")
                f.write(f"総JSTLタグ数: {sum(m.get('JSTL合計タグ数', 0) for m in self.metrics.values())}\n")
                f.write(f"総EL式数: {sum(m.get('EL式合計', 0) for m in self.metrics.values())}\n\n")
            
            # 問題統計
            if self.issues:
                f.write("【検出された問題】\n")
                issue_count = defaultdict(int)
                for issues in self.issues.values():
                    for issue in issues:
                        issue_count[issue['type']] += 1
                
                for issue_type, count in sorted(issue_count.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {issue_type}: {count}件\n")
                f.write("\n")
            
            # 使用率統計
            if self.metrics:
                files_with_scriptlets = sum(1 for m in self.metrics.values() if m.get('スクリプトレット数', 0) > 0)
                files_with_jstl = sum(1 for m in self.metrics.values() if m.get('JSTL合計タグ数', 0) > 0)
                files_with_el = sum(1 for m in self.metrics.values() if m.get('EL式合計', 0) > 0)
                
                f.write("【技術使用率】\n")
                f.write(f"スクリプトレット使用率: {files_with_scriptlets / len(self.metrics) * 100:.1f}%\n")
                f.write(f"JSTL使用率: {files_with_jstl / len(self.metrics) * 100:.1f}%\n")
                f.write(f"EL式使用率: {files_with_el / len(self.metrics) * 100:.1f}%\n\n")
            
            # 改善推奨事項
            f.write("【改善推奨事項】\n")
            if any(len(s) > 5 for s in self.scriptlets.values()):
                f.write("✓ スクリプトレットの削減を推奨\n")
            if self.security_issues:
                f.write("✓ セキュリティ脆弱性の修正が必要\n")
            if any(f['size'] > 30000 for f in self.jsp_files.values()):
                f.write("✓ 大きすぎるファイルの分割を推奨\n")
            
            f.write("\n" + "="*60 + "\n")
        
        print(f"サマリーレポートを {output_file} に保存しました")


def main():
    parser = argparse.ArgumentParser(
        description='統合版JSP解析ツール - JSPファイルの包括的な解析とレポート生成',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本的な使用（すべての形式でレポート生成）
  python jsp_analyzer_unified.py /path/to/project
  
  # CSV形式のみ生成
  python jsp_analyzer_unified.py /path/to/project --format csv
  
  # 出力ディレクトリを指定
  python jsp_analyzer_unified.py /path/to/project -o ./reports
  
  # 詳細ログを表示
  python jsp_analyzer_unified.py /path/to/project -v
        """
    )
    
    parser.add_argument('project_dir', help='解析対象のプロジェクトディレクトリ')
    parser.add_argument('-o', '--output-dir', default='./output', 
                        help='レポートの出力ディレクトリ（デフォルト: ./output）')
    parser.add_argument('-f', '--format', nargs='+', 
                        choices=['csv', 'markdown', 'json', 'text', 'all'],
                        default=['all'],
                        help='出力フォーマット（デフォルト: all）')
    parser.add_argument('-p', '--prefix', default='jsp_analysis',
                        help='出力ファイルのプレフィックス（デフォルト: jsp_analysis）')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='詳細なログを表示')
    
    args = parser.parse_args()
    
    # プロジェクトディレクトリの存在確認
    if not os.path.isdir(args.project_dir):
        print(f"エラー: {args.project_dir} は有効なディレクトリではありません。")
        sys.exit(1)
    
    # 出力ディレクトリの作成
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 解析実行
    analyzer = UnifiedJSPAnalyzer(args.project_dir, verbose=args.verbose)
    analyzer.analyze_project()
    
    # レポート生成
    # use prefix only for stable filenames (no timestamp)
    base_name = args.prefix
    
    formats = args.format if 'all' not in args.format else ['csv', 'markdown', 'json', 'text']
    
    print("\nレポート生成中...")
    # クラスタ計算とプロット生成（CSVにクラスタを追記し、プロットをoutputに保存）
    analyzer.compute_clusters_and_plot(args.output_dir)

    if 'csv' in formats:
        csv_file = os.path.join(args.output_dir, f"{base_name}.csv")
        analyzer.generate_csv_report(csv_file)
    # JSP呼び出し関係CSV
    calls_csv = os.path.join(args.output_dir, f"{base_name}_jsp_calls.csv")
    analyzer.generate_jsp_calls_csv(calls_csv)
    # include usage CSV/MD
    include_csv = os.path.join(args.output_dir, f"{base_name}_include_usage.csv")
    analyzer.generate_include_usage_csv(include_csv)
    
    if 'markdown' in formats:
        md_file = os.path.join(args.output_dir, f"{base_name}.md")
        analyzer.generate_markdown_report(md_file)
    # JSP呼び出し関係Markdown
    calls_md = os.path.join(args.output_dir, f"{base_name}_jsp_calls.md")
    analyzer.generate_jsp_calls_markdown(calls_md)
    include_md = os.path.join(args.output_dir, f"{base_name}_include_usage.md")
    analyzer.generate_include_usage_markdown(include_md)
    # include usage graph
    include_graph = os.path.join(args.output_dir, f"{base_name}_include_graph.png")
    analyzer.generate_include_graph(include_graph)
    
    if 'json' in formats:
        json_file = os.path.join(args.output_dir, f"{base_name}.json")
        analyzer.generate_json_report(json_file)
    
    if 'text' in formats:
        txt_file = os.path.join(args.output_dir, f"{base_name}_summary.txt")
        analyzer.generate_summary_text(txt_file)
    
    print("\n解析完了！")
    
    # 簡易サマリーを表示
    if analyzer.metrics:
        print(f"\n【解析結果サマリー】")
        print(f"総ファイル数: {len(analyzer.jsp_files)}")
        print(f"総コード行数: {sum(m.get('コード行数', 0) for m in analyzer.metrics.values()):,}")
        print(f"検出された問題: {sum(len(issues) for issues in analyzer.issues.values())}件")
        
        # 最も複雑なファイルを表示
        most_complex = max(analyzer.metrics.items(), 
                          key=lambda x: x[1].get('JSP複雑度指標', 0))
        if most_complex:
            file_name = os.path.basename(analyzer.jsp_files[most_complex[0]]['path'])
            complexity = most_complex[1].get('JSP複雑度指標', 0)
            print(f"最も複雑なファイル: {file_name} (複雑度: {complexity:.2f})")


if __name__ == "__main__":
    main()

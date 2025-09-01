#!/usr/bin/env python3
"""
SQLModel 타입 힌트 감사 스크립트
문제가 될 수 있는 타입 힌트를 찾아서 리포트합니다.
"""
import ast
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, get_origin, get_args

def is_class_type(t: Any) -> bool:
    """타입이 클래스인지 확인"""
    return isinstance(t, type)

def unwrap_type(t: Any) -> Any:
    """타입 래퍼를 해제하여 기저 타입을 추출"""
    origin = get_origin(t)
    if origin is None:
        return t
    
    # Annotated[T, ...] -> T
    if origin.__name__ == 'Annotated':
        args = get_args(t)
        return args[0] if args else t
    
    # Union[T, None] -> T
    if origin.__name__ == 'Union':
        args = get_args(t)
        for arg in args:
            if arg is not type(None):  # None이 아닌 첫 번째 타입
                return arg
        return t
    
    # List[T], Dict[K, V] 등 -> origin
    return origin

def audit_model_file(file_path: Path) -> List[Dict[str, Any]]:
    """모델 파일의 타입 힌트를 감사"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # SQLModel 클래스인지 확인
                bases = [base.id for base in node.bases if hasattr(base, 'id')]
                if 'SQLModel' in bases:
                    print(f"🔍 SQLModel 클래스 발견: {node.name}")
                    
                    # 클래스 변수들을 확인
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and item.annotation:
                            field_name = item.target.id if hasattr(item.target, 'id') else str(item.target)
                            
                            # 타입 힌트 추출
                            type_hint = ast.unparse(item.annotation)
                            
                            # 문제가 될 수 있는 패턴 체크
                            issues_found = []
                            
                            # 1. Dict + sa_column 조합
                            if 'Dict' in type_hint and 'sa_column' in ast.unparse(item):
                                issues_found.append("Dict 타입에 sa_column 사용")
                            
                            # 2. Optional 래퍼
                            if 'Optional' in type_hint:
                                issues_found.append("Optional 래퍼 사용")
                            
                            # 3. List 래퍼
                            if 'List' in type_hint:
                                issues_found.append("List 래퍼 사용")
                            
                            if issues_found:
                                issues.append({
                                    'file': str(file_path),
                                    'line': item.lineno,
                                    'class': node.name,
                                    'field': field_name,
                                    'type_hint': type_hint,
                                    'issues': issues_found
                                })
    
    except Exception as e:
        print(f"❌ 파일 분석 실패 {file_path}: {e}")
    
    return issues

def main():
    """메인 함수"""
    backend_dir = Path(__file__).parent.parent
    models_dir = backend_dir / 'models'
    
    print("🔍 SQLModel 타입 힌트 감사 시작...")
    print(f"📁 감사 대상: {models_dir}")
    
    all_issues = []
    
    # models 디렉토리의 모든 Python 파일 감사
    for py_file in models_dir.glob("*.py"):
        if py_file.name != "__init__.py":
            print(f"\n📄 분석 중: {py_file.name}")
            issues = audit_model_file(py_file)
            all_issues.extend(issues)
    
    # 결과 리포트
    print(f"\n{'='*60}")
    print("📊 감사 결과")
    print(f"{'='*60}")
    
    if not all_issues:
        print("✅ 문제가 될 수 있는 타입 힌트가 발견되지 않았습니다.")
    else:
        print(f"⚠️  {len(all_issues)}개의 잠재적 문제 발견:")
        
        for issue in all_issues:
            print(f"\n📍 {issue['file']}:{issue['line']}")
            print(f"   클래스: {issue['class']}")
            print(f"   필드: {issue['field']}")
            print(f"   타입: {issue['type_hint']}")
            print(f"   문제: {', '.join(issue['issues'])}")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    main()

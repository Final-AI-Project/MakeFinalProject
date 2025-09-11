# DB 트랜잭션은 core/database.py 에서 처리
# -> CRID 함수들은 commit()하지 않고 db.add()/flush()만 수행

# sqlalchemy 타입힌트 이슈로 인해 반환 타입 list -> Sequence로 명시 (반환은 자동으로 list로 변환됨)
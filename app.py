from flask import Flask, request,  jsonify,render_template, session , redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
import json
from sqlalchemy import inspect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'your_secret_key_here' 

db = SQLAlchemy(app)

# グローバル変数としてAAFCO基準値を定義
aafco_standards = {}

# 食材モデルの定義
class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    id = db.Column(db.Integer, primary_key=True)
    food_code = db.Column(db.Integer, nullable=False, unique=True)  # 食品番号を追加
    name = db.Column(db.String(80), nullable=False)
    ENERC_KCAL = db.Column(db.Float, nullable=False)
    WATER = db.Column(db.Float, nullable=False)
    ILE = db.Column(db.Float, nullable=False)
    LEU = db.Column(db.Float, nullable=False)
    LYS = db.Column(db.Float, nullable=False)
    MET = db.Column(db.Float, nullable=False)
    CYS = db.Column(db.Float, nullable=False)
    PHE = db.Column(db.Float, nullable=False)
    TYR = db.Column(db.Float, nullable=False)
    THR = db.Column(db.Float, nullable=False)
    TRP = db.Column(db.Float, nullable=False)
    VAL = db.Column(db.Float, nullable=False)
    HIS = db.Column(db.Float, nullable=False)
    ARG = db.Column(db.Float, nullable=False)
    F18D2N6 = db.Column(db.Float, nullable=False)
    F18D3N3 = db.Column(db.Float, nullable=False)
    F22D6N3 = db.Column(db.Float, nullable=False)
    NAT = db.Column(db.Float, nullable=False)
    K = db.Column(db.Float, nullable=False)
    CA = db.Column(db.Float, nullable=False)
    MG = db.Column(db.Float, nullable=False)
    P = db.Column(db.Float, nullable=False)
    FE = db.Column(db.Float, nullable=False)
    ZN = db.Column(db.Float, nullable=False)
    CU = db.Column(db.Float, nullable=False)
    MN = db.Column(db.Float, nullable=False)
    YO = db.Column(db.Float, nullable=False)
    SE = db.Column(db.Float, nullable=False)
    CR = db.Column(db.Float, nullable=False)
    RETOL = db.Column(db.Float, nullable=False)
    CARTA = db.Column(db.Float, nullable=False)
    CARTB = db.Column(db.Float, nullable=False)
    CRYPXB = db.Column(db.Float, nullable=False)
    CARTBEQ = db.Column(db.Float, nullable=False)
    VITA_RAE = db.Column(db.Float, nullable=False)
    VITD = db.Column(db.Float, nullable=False)
    TOCPHA = db.Column(db.Float, nullable=False)
    TOCPHB = db.Column(db.Float, nullable=False)
    TOCPHG = db.Column(db.Float, nullable=False)
    TOCPHD = db.Column(db.Float, nullable=False)
    THIA = db.Column(db.Float, nullable=False)
    RIBF = db.Column(db.Float, nullable=False)
    NIA = db.Column(db.Float, nullable=False)
    VITB6A = db.Column(db.Float, nullable=False)
    VITB12 = db.Column(db.Float, nullable=False)
    FOL = db.Column(db.Float, nullable=False)
    PANTAC = db.Column(db.Float, nullable=False)
    NACL_EQ = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Ingredientオブジェクトを辞書形式で返す"""
        return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name not in ['id', 'food_code', 'name']}

# AAFCO基準値をロードする関数
def load_aafco_standards():
    aafco_path = os.path.join(os.path.dirname(__file__), 'aafco_standards.xlsx')
    if not os.path.exists(aafco_path):
        print("AAFCO基準値のExcelファイルがありません")
        return {}
    df = pd.read_excel(aafco_path, engine='openpyxl')
    return {row["nutrient"]: row["minimum"] for _, row in df.iterrows()}

# 栄養素の合計を計算する関数
def calculate_totals(selected_list):
    nutrient_totals = {nutrient: 0 for nutrient in aafco_standards.keys()}
    for item in selected_list:
        food_code = item['food_code']
        grams = item['grams']
        nutrients = food_database.get(food_code, {})
        for nutrient, value in nutrients.items():
            nutrient_totals[nutrient] += value * (grams / 100)
    return nutrient_totals

# 不足栄養素に基づく提案食材を生成する関数
def suggest_ingredients_for_deficiencies(deficiencies):
    suggestions = {}
    for nutrient in deficiencies:
        if hasattr(Ingredient, nutrient):
            top_items = Ingredient.query.order_by(
                getattr(Ingredient, nutrient).desc()
            ).limit(15).all()
            suggestions[nutrient] = [
                {
                    "food_code": item.food_code,
                    "name": item.name,
                    "nutrients": {
                        col.name: getattr(item, col.name)
                        for col in Ingredient.__table__.columns
                        if col.name not in ['id', 'name', 'food_code']
                    },
                    "value": float(getattr(item, nutrient))
                }
                for item in top_items
            ]
    return suggestions

# 初期データベースの処理
def process_excel():
    excel_path = os.path.join(os.path.dirname(__file__), 'ingredients.xlsx')
    if not os.path.exists(excel_path):
        print("Excelファイル(ingredients.xlsx)が存在しません")
        return

    # Excelファイルの読み込み
    df = pd.read_excel(excel_path, engine='openpyxl')

    # データクレンジング: Tr, N/A, Undefined を 0 に置き換える
    df = df.replace(['Tr', 'N/A', 'Undefined', None], 0)

    # テーブルが存在しない場合に作成
    inspector = inspect(db.engine)
    if not inspector.has_table('ingredient'):
        db.create_all()

    # 既存データがある場合はスキップ
    if Ingredient.query.count() > 0:
        print("既存のデータがあります。処理をスキップします。")
        return

    # データベースへの登録
    for index, row in df.iterrows():
        ingredient = Ingredient(
            category=row["食品群"],  # Excelからカテゴリを読み取る
            food_code=int(row["食品番号"]),
            name=row["食品名"],
            ENERC_KCAL=float(row["エネルギー"]),
            WATER=float(row["水分"]),
            ILE=float(row["イソロイシン"]),
            LEU=float(row["ロイシン"]),
            LYS=float(row["リシン（リジン）"]),
            MET=float(row["メチオニン"]),
            CYS=float(row["シスチン"]),
            PHE=float(row["フェニルアラニン"]),
            TYR=float(row["チロシン"]),
            THR=float(row["トレオニン（スレオニン）"]),
            TRP=float(row["トリプトファン"]),
            VAL=float(row["バリン"]),
            HIS=float(row["ヒスチジン"]),
            ARG=float(row["アルギニン"]),
            F18D2N6=float(row["リノール酸"]),
            F18D3N3=float(row["α‐リノレン酸"]),
            F22D6N3=float(row["ドコサヘキサエン酸"]),
            NAT=float(row["ナトリウム"]),
            K=float(row["カリウム"]),
            CA=float(row["カルシウム"]),
            MG=float(row["マグネシウム"]),
            P=float(row["リン"]),
            FE=float(row["鉄"]),
            ZN=float(row["亜鉛"]),
            CU=float(row["銅"]),
            MN=float(row["マンガン"]),
            YO=float(row["ヨウ素"]),
            SE=float(row["セレン"]),
            CR=float(row["クロム"]),
            RETOL=float(row["VAレチノール"]),
            CARTA=float(row["VAα|カロテン"]),
            CARTB=float(row["VAβ|カロテン"]),
            CRYPXB=float(row["VＡβ|クリプトキサンチン"]),
            CARTBEQ=float(row["ＶＡβ|カロテン当量"]),
            VITA_RAE=float(row["ＶＡレチノール活性当量"]),
            VITD=float(row["ビタミンD"]),
            TOCPHA=float(row["VEα|トコフェロール"]),
            TOCPHB=float(row["VEβ|トコフェロール"]),
            TOCPHG=float(row["VEγ|トコフェロール"]),
            TOCPHD=float(row["VEδ|トコフェロール"]),
            THIA=float(row["ビタミンB1"]),
            RIBF=float(row["ビタミンB2"]),
            NIA=float(row["ナイアシン"]),
            VITB6A=float(row["ビタミンB6"]),
            VITB12=float(row["ビタミンB12"]),
            FOL=float(row["葉酸"]),
            PANTAC=float(row["パントテン酸"]),
            NACL_EQ=float(row["食塩相当量"]),
        )
        try:
            db.session.add(ingredient)
            db.session.commit()
        except Exception as e:
            print(f"行 {index} でエラーが発生しました: {e}")
            db.session.rollback()

# nutrient_labels をグローバル変数として定義
nutrient_labels = {
    'ENERC_KCAL': ('エネルギー', 'kcal'),
    'WATER': ('水分', 'g'),
    'ILE': ('イソロイシン', 'g'),
    'LEU': ('ロイシン', 'g'),
    'LYS': ('リシン（リジン）', 'g'),
    'MET': ('メチオニン', 'g'),
    'CYS': ('シスチン', 'g'),
    'PHE': ('フェニルアラニン', 'g'),
    'TYR': ('チロシン', 'g'),
    'THR': ('トレオニン（スレオニン）', 'g'),
    'TRP': ('トリプトファン', 'g'),
    'VAL': ('バリン', 'g'),
    'HIS': ('ヒスチジン', 'g'),
    'ARG': ('アルギニン', 'g'),
    'F18D2N6': ('リノール酸', 'g'),
    'F18D3N3': ('α-リノレン酸', 'g'),
    'F22D6N3': ('ドコサヘキサエン酸', 'g'),
    'NAT': ('ナトリウム', 'g'),
    'K': ('カリウム', 'g'),
    'CA': ('カルシウム', 'g'),
    'MG': ('マグネシウム', 'g'),
    'P': ('リン', 'g'),
    'FE': ('鉄', 'g'),
    'ZN': ('亜鉛', 'g'),
    'CU': ('銅', 'g'),
    'MN': ('マンガン', 'g'),
    'YO': ('ヨウ素', 'g'),
    'SE': ('セレン', 'g'),
    'CR': ('クロム', 'g'),
    'RETOL': ('レチノール', 'g'),
    'CARTA': ('α-カロテン', 'g'),
    'CARTB': ('β-カロテン', 'g'),
    'CRYPXB': ('クリプトキサンチン', 'g'),
    'CARTBEQ': ('カロテン当量', 'g'),
    'VITA_RAE': ('レチノール活性当量', 'g'),
    'VITD': ('ビタミンD', 'g'),
    'TOCPHA': ('α-トコフェロール', 'g'),
    'TOCPHB': ('β-トコフェロール', 'g'),
    'TOCPHG': ('γ-トコフェロール', 'g'),
    'TOCPHD': ('δ-トコフェロール', 'g'),
    'THIA': ('ビタミンB1', 'g'),
    'RIBF': ('ビタミンB2', 'g'),
    'NIA': ('ナイアシン', 'g'),
    'VITB6A': ('ビタミンB6', 'g'),
    'VITB12': ('ビタミンB12', 'g'),
    'FOL': ('葉酸', 'g'),
    'PANTAC': ('パントテン酸', 'g'),
    'NACL_EQ': ('食塩相当量', 'g')
}

# 共通ユーティリティ関数
def calculate_nutrients(selected_list):
    """
    栄養素の合計を計算する関数
    """
    nutrient_totals = {nutrient: 0 for nutrient in aafco_standards.keys()}
    for item in selected_list:
        ingredient = Ingredient.query.filter_by(food_code=item['food_code']).first()
        if ingredient:
            for nutrient in aafco_standards.keys():
                value = getattr(ingredient, nutrient, 0) or 0
                nutrient_totals[nutrient] += value * (item['grams'] / 100)
        else:
            print(f"Warning: Ingredient with food_code {item['food_code']} not found")
    return nutrient_totals

# エンドポイントの定義
@app.route('/')
def index():
    # `index.html` に食材リストを表示
    ingredients = Ingredient.query.all()
    return render_template('index.html', ingredients=ingredients)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # JSON データの取得
        data = request.get_json()
        print("Received data:", data)

        # selected_list を取得しセッションに保存
        session['selected_list'] = data.get('selected_list', [])
        print("Session updated with selected_list:", session['selected_list'])  # デバッグ用

        selected_list = session['selected_list']


        # 食材コードリストの作成
        selected_food_codes = [int(item['food_code']) for item in selected_list]
        print("Selected food codes:", selected_food_codes)

        # データベースから選択された食材を取得
        selected_ingredients = Ingredient.query.filter(Ingredient.food_code.in_(selected_food_codes)).all()
        print("Selected ingredients:", selected_ingredients)

        totals = {nutrient: 0 for nutrient in aafco_standards.keys()}
        total_grams = 0
        selected_list_tuples = []

        for item in selected_list:
            food_code = int(item['food_code'])
            grams = float(item['grams'])

            # 対応する食材を取得
            ingredient = next((ing for ing in selected_ingredients if ing.food_code == food_code), None)
            if ingredient:
                selected_list_tuples.append((food_code, grams, ingredient.name))
                total_grams += grams
                for nutrient in aafco_standards.keys():
                    nutrient_value = getattr(ingredient, nutrient, 0) or 0
                    totals[nutrient] += nutrient_value * (grams / 100)

        # 不足栄養素を特定
        deficiencies = [nutrient for nutrient, value in totals.items() if value < aafco_standards.get(nutrient, 0)]

        # 提案食材を取得
        suggestions = suggest_ingredients_for_deficiencies(deficiencies)

        return render_template(
            'calculate.html',
            totals=totals,
            selected_list=selected_list_tuples,
            total_grams=total_grams,
            deficiencies=deficiencies,
            suggestions=suggestions,
            result_symbols={
                nutrient: "×" if totals[nutrient] < aafco_standards.get(nutrient, 0) else "○" for nutrient in totals
            },
            nutrient_labels=nutrient_labels,
            aafco_standards=aafco_standards
        )
    except Exception as e:
        print(f"Unhandled Exception in /calculate: {e}")
        return jsonify({"error": str(e)}), 500

def suggest_best_ingredients(deficiencies):
    """
    不足している複数の栄養素を部分的にでも補える食材を提案する
    """
    best_suggestions = []

    # すべての食材を取得
    all_ingredients = Ingredient.query.all()

    for ingredient in all_ingredients:
        total_score = 0
        partial_score = 0
        covered_nutrients = []

        for nutrient in deficiencies:
            nutrient_value = getattr(ingredient, nutrient, 0) or 0
            standard_value = aafco_standards.get(nutrient, 0)

            if standard_value > 0 and nutrient_value > 0:
                partial_score = min(nutrient_value / standard_value, 1.0)  # カバー率を1.0で最大化
                total_score += partial_score
                covered_nutrients.append(nutrient)

        # スコアがゼロでない食材を提案候補に追加
        if total_score > 0:
            best_suggestions.append({
                "food_code": ingredient.food_code,
                "name": ingredient.name,
                "score": round(total_score, 2),
                "covered_nutrients": covered_nutrients
            })

    # スコア順に並べて上位5つを返す
    return sorted(best_suggestions, key=lambda x: x['score'], reverse=True)[:5]


# データ処理を行う関数
def process_adjust(data):
    print("=== process_adjust関数が呼び出されました ===")  # 確認用ログ
    print("受け取ったデータ:", data)  # 受け取ったJSONデータを出力
    
    # JSONデータから情報を取得
    selected_list = data.get('selected_list', [])
    deficiencies = data.get('deficiencies', [])
    print("Deficiencies:", deficiencies)

    # `selected_list` の形式を確認し、正しい形式に変換
    if isinstance(selected_list, list) and isinstance(selected_list[0], list):
        selected_list = [{"food_code": item[0], "grams": item[1], "name": item[2]} for item in selected_list]
    elif not (isinstance(selected_list, list) and isinstance(selected_list[0], dict)):
        raise ValueError("Invalid format for selected_list")

    print("Processed selected_list:", selected_list)

    # 選択した食材のデータベースオブジェクトを取得
    selected_food_codes = [item['food_code'] for item in selected_list]
    selected_ingredients = Ingredient.query.filter(Ingredient.food_code.in_(selected_food_codes)).all()

    # 栄養素の合計を計算
    nutrient_totals = {nutrient: 0 for nutrient in aafco_standards.keys()}
    for item in selected_list:
        food_code = item['food_code']
        grams = float(item['grams'])
        ingredient = next((ing for ing in selected_ingredients if ing.food_code == food_code), None)
        if ingredient:
            for nutrient in aafco_standards.keys():
                value = getattr(ingredient, nutrient, 0) or 0
                nutrient_totals[nutrient] += value * (grams / 100)

    # 不足栄養素に対する提案食材を取得
    suggestions = {}
    for nutrient in deficiencies:
        ingredients = (
            Ingredient.query.filter(getattr(Ingredient, nutrient, 0) > 0)
            .order_by(getattr(Ingredient, nutrient).desc())
            .limit(5)
            .all()
        )
        suggestions[nutrient] = [
            {
                "food_code": ing.food_code,
                "name": ing.name,
                "value": getattr(ing, nutrient, 0),
                "nutrients": {n: getattr(ing, n, 0) for n in aafco_standards.keys()},
            }
            for ing in ingredients
        ]

    # 不足栄養素を複数補える提案食材を追加
    best_suggestions = suggest_best_ingredients(deficiencies)

    # 適合状況を計算
    result_symbols = {
        nutrient: "×" if nutrient_totals.get(nutrient, 0) < aafco_standards.get(nutrient, 0) else "○"
        for nutrient in aafco_standards
    }

    # JSONレスポンス生成
    return {
        "selected_ingredients": selected_list,
        "nutrient_totals": nutrient_totals,
        "deficiencies": deficiencies,
        "suggestions": suggestions,
        "best_suggestions": best_suggestions,  # 複数栄養素を補える最適食材
        "result_symbols": result_symbols,
        "nutrient_labels": nutrient_labels,
        "aafco_standards": aafco_standards
    }

def calculate_nutrients(selected_list):
    nutrient_totals = {nutrient: 0 for nutrient in aafco_standards.keys()}
    for item in selected_list:
        ingredient = Ingredient.query.filter_by(food_code=item['food_code']).first()
        if ingredient:
            for nutrient in aafco_standards.keys():
                value = getattr(ingredient, nutrient, 0) or 0
                nutrient_totals[nutrient] += value * (item['grams'] / 100)
        else:
            print(f"Warning: Ingredient with food_code {item['food_code']} not found")
    return nutrient_totals


@app.route('/adjust', methods=['GET', 'POST'])
def adjust():
    # GET処理
    if request.method == 'GET':
        try:
            # セッションからデータを取得
            selected_list = session.get('selected_list', [])
            print("Session selected_list:", selected_list)  # デバッグ用

            # デフォルトの食材リストを設定（セッションにデータがない場合のみ）
            if not selected_list:
                default_ingredients = Ingredient.query.limit(3).all()
                selected_list = [
                    {'food_code': ing.food_code, 'grams': 100, 'name': ing.name}
                    for ing in default_ingredients
                ]
                session['selected_list'] = selected_list  # 初期データをセッションに保存

            # 選択された食材情報をデータベースから取得
            selected_food_codes = [item['food_code'] for item in selected_list]
            ingredients = Ingredient.query.filter(Ingredient.food_code.in_(selected_food_codes)).all()

            # 選択されたリストを整形（セッションのグラム値を優先）
            selected_list = [
                {
                    'food_code': ing.food_code,
                    'grams': next((item['grams'] for item in selected_list if str(item['food_code']) == str(ing.food_code)), 100),
                    'name': ing.name
                }
                for ing in ingredients
            ]
            print("Adjusted selected_list:", selected_list)  # デバッグ用

            # 栄養素合計を計算
            nutrient_totals = calculate_nutrients(selected_list)

            # 不足栄養素を判定
            deficiencies = [
                nutrient for nutrient, total in nutrient_totals.items()
                if total < aafco_standards.get(nutrient, 0)
            ]

            # 提案食材を生成
            suggestions = suggest_ingredients_for_deficiencies(deficiencies)

            # 合計グラム数を計算
            total_grams = sum(item['grams'] for item in selected_list)

            # レスポンスデータ生成
            response_data = {
                "selected_ingredients": selected_list,
                "nutrient_totals": nutrient_totals,
                "deficiencies": deficiencies,
                "suggestions": suggestions,
                "available_ingredients": [
                    {'food_code': ing.food_code, 'name': ing.name} for ing in Ingredient.query.all()
                ],
                "result_symbols": {
                    nutrient: "×" if nutrient_totals[nutrient] < aafco_standards[nutrient] else "○"
                    for nutrient in aafco_standards
                },
                "total_grams": total_grams,  # 合計グラム数を追加
                "nutrient_labels": nutrient_labels,
                "aafco_standards": aafco_standards,
            }

            return render_template('adjust.html', data=response_data)

        except Exception as e:
            print(f"Error in GET /adjust: {e}")
            return render_template('adjust.html', data={})

    # POST処理
    if request.method == 'POST':
        try:
            # POSTリクエストで受信したデータをセッションに保存
            data = request.json
            print("Received POST data:", data)  # デバッグ用
            session['selected_list'] = data.get('selected_ingredients', [])
            return jsonify({"message": "Data received successfully"})
        except Exception as e:
            print(f"Error in POST /adjust: {e}")
            return jsonify({"error": str(e)}), 500

@app.route('/calculate-nutrients', methods=['POST'])
def calculate_nutrients_endpoint():
    """
    栄養素を計算するエンドポイント。
    フロントエンドから送信された食材リストを基に、各栄養素の合計値を計算する。
    """
    try:
        # フロントエンドから送信されたデータを取得
        data = request.json
        selected_ingredients = data.get('selected_ingredients', [])

        # 栄養素の合計を初期化
        nutrient_totals = {nutrient: 0 for nutrient in aafco_standards.keys()}

        # 各食材について栄養素を計算
        for item in selected_ingredients:
            food_code = item.get('food_code')
            grams = item.get('grams', 0)

            # データベースから該当する食材を取得
            ingredient = Ingredient.query.filter_by(food_code=food_code).first()
            if not ingredient:
                print(f"Warning: Ingredient with food_code {food_code} not found.")
                continue

            # 栄養素を計算して加算
            for nutrient in nutrient_totals.keys():
                value_per_100g = getattr(ingredient, nutrient, 0) or 0
                nutrient_totals[nutrient] += value_per_100g * (grams / 100)

        # 計算結果を返す
        return jsonify({"nutrient_totals": nutrient_totals})

    except Exception as e:
        print(f"Error in /calculate-nutrients: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/recalculate', methods=['POST'])
def recalculate():
    try:
        data = request.json
        print("Received Data for Recalculate:", data)

        selected_list = data.get('selected_ingredients', [])

        # データ形式を検証
        if not all(isinstance(item, dict) and 'food_code' in item and 'grams' in item for item in selected_list):
            raise ValueError("Invalid data format for selected_ingredients")

        # 栄養素の合計を計算
        nutrient_totals = calculate_totals(selected_list)

        # 不足栄養素の判定
        deficiencies = [
            nutrient for nutrient, total in nutrient_totals.items()
            if total < aafco_standards.get(nutrient, 0)
        ]

        # 提案食材の再生成
        suggestions = suggest_ingredients_for_deficiencies(deficiencies)

        return jsonify({
            "nutrient_totals": nutrient_totals,
            "deficiencies": deficiencies,
            "suggestions": suggestions
        })

    except Exception as e:
        print(f"Error in POST /recalculate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ingredients', methods=['GET'])
def get_ingredients():
    """
    全食材リストを取得するエンドポイント。
    """
    try:
        ingredients = Ingredient.query.all()
        results = [{"food_code": ing.food_code, "name": ing.name} for ing in ingredients]
        return jsonify({"ingredients": results})
    except Exception as e:
        print(f"全食材リスト取得エラー: {e}")
        return jsonify({"error": str(e)}), 500

# Helper functions
def calculate_totals(selected_list):
    """選択された食材リストに基づいて栄養素の合計を計算"""
    print("Calculating totals for:", selected_list)
    nutrient_totals = {nutrient: 0 for nutrient in aafco_standards.keys()}
    for item in selected_list:
        food_code = item.get('food_code')
        grams = item.get('grams', 0)
        ingredient = Ingredient.query.filter_by(food_code=food_code).first()
        if ingredient:
            for nutrient in aafco_standards.keys():
                value = getattr(ingredient, nutrient, 0) or 0
                nutrient_totals[nutrient] += value * (grams / 100)
        else:
            print(f"Warning: Ingredient with food_code {food_code} not found")
    print("Nutrient totals:", nutrient_totals)
    return nutrient_totals

@app.route('/search-ingredients', methods=['GET'])
def search_ingredients():
    """
    食材検索エンドポイント。
    クエリ文字列を使用して、食材名を部分一致で検索します。
    """
    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify({"ingredients": []})

    ingredients = Ingredient.query.filter(Ingredient.name.ilike(f"%{query}%")).all()
    results = [{"food_code": ing.food_code, "name": ing.name} for ing in ingredients]
    return jsonify({"ingredients": results})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        process_excel()  # データベース初期化
        aafco_standards = load_aafco_standards()
        print("AAFCO Standards Loaded:", aafco_standards)  # デバッグログ

    # アプリケーションの起動
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)



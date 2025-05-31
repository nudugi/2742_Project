from flask import Flask, request, render_template, jsonify, send_from_directory
from openai import OpenAI
import os

app = Flask(__name__, template_folder='templates')
# `os.environ.get("OPENAI_API_KEY")`는 함수 내에서 호출 시점마다 가져오도록 변경되었습니다.
# 따라서 이 전역 변수 설정은 더 이상 필요 없습니다.


# --- 메인 웹사이트 (27.42 랜딩 페이지)를 서비스하는 라우트 ---
@app.route('/')
def serve_main_site():
    # Repl.it 프로젝트의 루트 디렉토리에 있는 index.html을 반환
    # (사용자가 제공한 27.42 웹사이트 코드가 이 파일에 있을 것으로 가정)
    return send_from_directory('.', 'index.html')


# --- AI 생성기 페이지를 서비스하는 라우트 ---
@app.route('/generator', methods=['GET'])  # 경로를 /generator로 변경했습니다.
def show_generator():
    return render_template('index.html')  # templates 폴더 안의 AI 생성기 HTML


@app.route('/generate', methods=['POST'])
def generate_text():
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API Key is not set. Please set it in Repl.it Secrets.")

        client = OpenAI(api_key=api_key)

        exhibition_title = request.form['exhibition_title']
        exhibition_theme = request.form['exhibition_theme']
        artist_name = request.form['artist_name']
        work_description = request.form['work_description']
        exhibition_intent = request.form['exhibition_intent']
        additional_info = request.form.get('additional_info', '')

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 또는 더 고급 모델인 "gpt-4" (비용 증가)
            messages=[
                {
                    "role":
                    "system",
                    "content":
                    "당신은 전문적인 미술 평론가이자 전시기획자입니다. 제공된 정보를 바탕으로 심도 깊고 상세한 작가노트, 전시 서문, 작품 설명을 작성해 주세요. 각 섹션은 독립적인 문단으로 구성하며, 독자들이 예술가의 의도와 작품 세계를 깊이 이해할 수 있도록 풍부한 내용을 담아주십시오. 결과물은 '작가노트:', '전시 서문:', '작품 설명:'으로 명확히 구분하여 작성합니다."
                },
                {
                    "role":
                    "user",
                    "content":
                    f"전시 제목: {exhibition_title}\n전시 주제: {exhibition_theme}\n작가 이름: {artist_name}\n작품 설명: {work_description}\n전시 의도: {exhibition_intent}\n추가 정보: {additional_info}\n\n결과물은 다음 형식으로 부탁드립니다:\n작가노트:\n[작가노트 내용]\n\n전시 서문:\n[전시 서문 내용]\n\n작품 설명:\n[작품 설명 내용]"
                },
            ],
            max_tokens=1500,  # 생성되는 텍스트의 길이를 늘렸습니다.
            temperature=0.7,
        )

        generated_text = response.choices[0].message.content.strip()

        # 새로운 파싱 로직: '작가노트:', '전시 서문:', '작품 설명:' 기준으로 분리
        artist_note = ""
        exhibition_preface = ""
        work_explanation = ""

        # 첫 번째 분리: 작가노트
        parts_artist_note = generated_text.split("작가노트:", 1)
        if len(parts_artist_note) > 1:
            temp_text = parts_artist_note[1]

            # 두 번째 분리: 전시 서문
            parts_exhibition_preface = temp_text.split("전시 서문:", 1)
            artist_note = parts_exhibition_preface[0].strip() if len(
                parts_exhibition_preface) > 0 else ""

            if len(parts_exhibition_preface) > 1:
                temp_text_2 = parts_exhibition_preface[1]

                # 세 번째 분리: 작품 설명
                parts_work_explanation = temp_text_2.split("작품 설명:", 1)
                exhibition_preface = parts_work_explanation[0].strip() if len(
                    parts_work_explanation) > 0 else ""

                if len(parts_work_explanation) > 1:
                    work_explanation = parts_work_explanation[1].strip()

        # 만약 "작가노트:", "전시 서문:", "작품 설명:" 키워드가 없는 경우 전체를 하나로 처리
        if not artist_note and not exhibition_preface and not work_explanation:
            artist_note = generated_text  # 전체 내용을 작가노트로 할당하거나, 사용자에게 오류 알림

        if not artist_note and "작가노트:" in generated_text:
            artist_note = generated_text.split("작가노트:", 1)[1].split(
                "전시 서문:", 1)[0].strip() if "전시 서문:" in generated_text.split(
                    "작가노트:", 1)[1] else generated_text.split("작가노트:",
                                                             1)[1].strip()
        if not exhibition_preface and "전시 서문:" in generated_text:
            exhibition_preface = generated_text.split("전시 서문:", 1)[1].split(
                "작품 설명:", 1)[0].strip() if "작품 설명:" in generated_text.split(
                    "전시 서문:", 1)[1] else generated_text.split("전시 서문:",
                                                              1)[1].strip()
        if not work_explanation and "작품 설명:" in generated_text:
            work_explanation = generated_text.split("작품 설명:", 1)[1].strip()

        return jsonify({
            'artist_note': artist_note,
            'exhibition_preface': exhibition_preface,
            'work_explanation': work_explanation
        })

    except Exception as e:
        print(f"Error during generation: {e}")  # 디버깅을 위해 에러 출력
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

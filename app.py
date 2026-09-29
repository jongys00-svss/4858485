import streamlit as st

from translator import TranslationError, create_client, get_api_key, get_model, translate

RESULT_LABELS = {"en": "🇺🇸 English", "ja": "🇯🇵 日本語", "vi": "🇻🇳 Tiếng Việt"}

st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="wide")

api_key = get_api_key()
model = get_model()


@st.cache_resource
def get_client(key: str):
    return create_client(key)


def clear():
    st.session_state["input_text"] = ""
    st.session_state.pop("result", None)


with st.sidebar:
    st.header("⚙ 설정")
    st.write(f"모델: `{model}`")
    st.write(f"API 키: {'✅ 설정됨' if api_key else '❌ 없음'}")
    st.button("지우기", on_click=clear, width="stretch")

st.title("🌐 다국어 번역기")
st.caption("영어 · 일본어 · 베트남어로 한 번에 번역합니다.")

if not api_key:
    st.error("API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
    st.stop()

with st.form("translate_form"):
    st.text_area(
        "번역할 텍스트",
        key="input_text",
        height=150,
        placeholder="번역할 텍스트를 입력하세요...",
        label_visibility="collapsed",
    )
    with st.container(horizontal=True, horizontal_alignment="right"):
        submitted = st.form_submit_button("번역하기 (Ctrl+Enter)", type="primary")

if submitted:
    text = st.session_state["input_text"]
    if not text.strip():
        st.warning("텍스트를 입력하세요.")
    else:
        try:
            with st.spinner("번역 중..."):
                translations = translate(get_client(api_key), text, model)
            st.session_state["result"] = {"source": text, "translations": translations}
        except TranslationError as e:
            st.error(str(e))

st.divider()

result = st.session_state.get("result")
if not result:
    st.info("텍스트를 입력하고 번역하기를 누르면 결과가 여기에 표시됩니다.")
else:
    st.subheader("📝 입력한 텍스트")
    st.code(result["source"], language=None, wrap_lines=True)

    for col, (lang, label) in zip(st.columns(3), RESULT_LABELS.items()):
        with col, st.container(border=True):
            st.markdown(f"**{label}**")
            st.code(result["translations"][lang], language=None, wrap_lines=True)

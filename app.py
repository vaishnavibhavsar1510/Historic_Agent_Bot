# app.py  ──────────────────────────────────────────────────────────────
import os, re, streamlit as st
from dotenv import load_dotenv

load_dotenv()                                            # local .env for dev

# ── Inject the key for LangChain/OpenAI helpers ───────────────────────
os.environ["OPENAI_API_KEY"] = (
    os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
)

# ── Local helpers ─────────────────────────────────────────────────────
from backend.app.otp import (
    generate_otp, store_otp, retrieve_stored_otp,
    delete_otp, find_email,
)
from backend.app.email_utils import send_otp_email, send_plain_email
from backend.app.monument_search import answer_monument_query

# ── Page config & CSS (use your existing big CSS block) ───────────────
st.set_page_config(page_title="Historical Monument Agent",
                   page_icon="🏛️", layout="centered")
st.markdown("""<style> … YOUR  CSS  BLOCK … </style>""",
            unsafe_allow_html=True)

# ── Session-state defaults ────────────────────────────────────────────
for k, v in {
    "messages": [],
    "awaiting_email": False,
    "awaiting_otp": False,
    "otp_attempts": 0,
    "email": None,
    "last_monument_query": None,
    "user_input": None,
}.items():
    st.session_state.setdefault(k, v)

# ── Chat-bubble helper ────────────────────────────────────────────────
def bubble(role: str, text: str):
    avatar = "🤖" if role == "assistant" else None
    with st.chat_message(role, avatar=avatar):
        st.markdown(text)

# ── Main loop ─────────────────────────────────────────────────────────
def main() -> None:
    st.title("🏛️ Historical Monument Agent")

    # 1) greet on first load
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hey there 👋  Ask me about any historical monument!"
        })

    # 2) replay history
    for m in st.session_state.messages:
        bubble(m["role"], m["content"])

    # 3) free-text input (hidden while OTP form showing)
    fresh_text = None
    if not st.session_state.awaiting_otp:
        prompt = "Enter your e-mail address…" if st.session_state.awaiting_email else "Message…"
        fresh_text = st.chat_input(prompt)

    if fresh_text:
        st.session_state.messages.append({"role": "user", "content": fresh_text})
        st.session_state.user_input = fresh_text
        bubble("user", fresh_text)

    # 4) OTP form
    if st.session_state.awaiting_otp:
        with st.form("otp_form"):
            otp_code = st.text_input("Enter the 6-digit code:")
            c1, c2 = st.columns(2)
            verify = c1.form_submit_button("Verify OTP")
            cancel = c2.form_submit_button("Cancel")

            if cancel:
                st.session_state.update(awaiting_email=False,
                                        awaiting_otp=False,
                                        otp_attempts=0,
                                        email=None,
                                        user_input=None)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Email verification cancelled. How else can I help?"
                })
                st.rerun()                                   # refresh UI
            if verify and otp_code:
                st.session_state.user_input = otp_code       # go to core logic
                # fall through

    # 5) nothing to do?
    if st.session_state.user_input is None:
        return

    txt = st.session_state.user_input.strip()
    st.session_state.user_input = None                      # consume

    # ── (A) waiting for e-mail ────────────────────────────────────────
    if st.session_state.awaiting_email:
        email = find_email(txt)
        if email:
            st.session_state.email = email
            st.session_state.awaiting_email = False

            code = generate_otp()
            store_otp(email, code)

            if send_otp_email(email, code):
                st.session_state.awaiting_otp = True
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "✅ OTP sent! Please enter the 6-digit code below."
                })
                st.rerun()                                   # ► show the OTP form immediately
            else:
                st.session_state.awaiting_email = True
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "⚠️ Couldn't send OTP. Please double-check the address."
                })
                st.rerun()
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "⚠️ I didn’t catch a valid e-mail. Please try again."
            })
            st.rerun()
        return  # we've already rerun or will display message next cycle

    # ── (B) waiting for OTP ──────────────────────────────────────────
    if st.session_state.awaiting_otp:
        if re.fullmatch(r"\d{6}", txt):
            stored = retrieve_stored_otp(st.session_state.email)
            if stored and txt == stored:
                # success
                delete_otp(st.session_state.email)
                st.session_state.awaiting_otp = False
                st.session_state.otp_attempts = 0
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "✅ Verified! I’ll e-mail you a detailed guide shortly."
                })

                if st.session_state.last_monument_query:
                    guide = answer_monument_query(
                        st.session_state.last_monument_query
                        + "\nPlease give me a more detailed guide."
                    )
                    send_plain_email(
                        st.session_state.email,
                        f"Guide: {st.session_state.last_monument_query.title()}",
                        guide
                    )
                st.rerun()                                   # ► hide OTP form instantly
            else:
                st.session_state.otp_attempts += 1
                msg = "❌ Incorrect code. Please try again."
                if not stored or st.session_state.otp_attempts >= 3:
                    msg = "❌ Verification failed or OTP expired. Please send your e-mail again."
                    st.session_state.update(awaiting_email=True,
                                            awaiting_otp=False,
                                            otp_attempts=0)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.rerun()
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "⚠️ Please enter exactly six digits."
            })
            st.rerun()
        return

    # ── (C) fresh monument question ───────────────────────────────────
    st.session_state.last_monument_query = txt
    with st.spinner("🔍 Searching monument database…"):
        answer = answer_monument_query(txt)

    st.session_state.awaiting_email = True
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            answer +
            "\n\nIf you’d like more details emailed, please tell me your e-mail address."
        )
    })
    st.rerun()                                               # prompt for e-mail

# ── run ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()

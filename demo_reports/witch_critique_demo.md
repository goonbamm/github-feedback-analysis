## 🔮 마녀의 독설

> 수정 구슬이 보여주는 너의 약점들... 귀 기울여 들어봐.

_🔮 자, 수정 구슬을 들여다보니... 흠, 개선할 게 좀 보이는군._

<div style="border-left: 4px solid #8b0000; background: linear-gradient(135deg, #2b0000 0%, #1a1a2e 100%); padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
    <h3 style="margin: 0; color: #e0e0e0; font-size: 1.2em;">커밋 메시지</h3>
    <span style="background: #8b0000; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">🔥 치명적</span>
  </div>
  <div style="color: #ff6b9d; font-size: 1.1em; font-weight: 500; margin-bottom: 16px; line-height: 1.6;">
    💬 커밋 메시지의 45%가 형편없어. '수정', 'fix', 'update' 같은 게 전부야? 6개월 후 너 자신도 뭘 고쳤는지 모를 텐데.
  </div>
  <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 4px; margin-bottom: 12px;">
    <div style="color: #9ca3af; font-size: 0.9em; margin-bottom: 4px;"><strong>📊 증거:</strong></div>
    <div style="color: #d1d5db;">150개 커밋 중 68개가 불량</div>
  </div>
  <div style="background: rgba(139,0,0,0.2); padding: 12px; border-radius: 4px; margin-bottom: 12px;">
    <div style="color: #fca5a5; font-size: 0.9em; margin-bottom: 4px;"><strong>⚠️ 결과:</strong></div>
    <div style="color: #fecaca;">나중에 버그 찾느라 git log 보면서 시간 낭비할 거야. 팀원들도 네 변경사항 이해 못 해.</div>
  </div>
  <div style="background: rgba(34,197,94,0.15); padding: 12px; border-radius: 4px;">
    <div style="color: #86efac; font-size: 0.9em; margin-bottom: 4px;"><strong>💊 처방:</strong></div>
    <div style="color: #bbf7d0;">커밋 메시지에 '왜'를 담아. 'fix: 로그인 시 토큰 만료 체크 누락 수정' 이런 식으로.</div>
  </div>
</div>

<div style="border-left: 4px solid #b8860b; background: linear-gradient(135deg, #2b1d00 0%, #1a1a2e 100%); padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
    <h3 style="margin: 0; color: #e0e0e0; font-size: 1.2em;">PR 크기</h3>
    <span style="background: #b8860b; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">⚡ 심각</span>
  </div>
  <div style="color: #ff6b9d; font-size: 1.1em; font-weight: 500; margin-bottom: 16px; line-height: 1.6;">
    💬 PR 하나에 평균 850줄? 리뷰어들 괴롭히는 게 취미야? 큰 PR은 안 읽힌다는 거 몰라?
  </div>
  <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 4px; margin-bottom: 12px;">
    <div style="color: #9ca3af; font-size: 0.9em; margin-bottom: 4px;"><strong>📊 증거:</strong></div>
    <div style="color: #d1d5db;">12개 PR이 1000줄 이상</div>
  </div>
  <div style="background: rgba(139,0,0,0.2); padding: 12px; border-radius: 4px; margin-bottom: 12px;">
    <div style="color: #fca5a5; font-size: 0.9em; margin-bottom: 4px;"><strong>⚠️ 결과:</strong></div>
    <div style="color: #fecaca;">리뷰 품질 떨어지고, 버그 놓치고, 머지 충돌 지옥에 빠질 거야.</div>
  </div>
  <div style="background: rgba(34,197,94,0.15); padding: 12px; border-radius: 4px;">
    <div style="color: #86efac; font-size: 0.9em; margin-bottom: 4px;"><strong>💊 처방:</strong></div>
    <div style="color: #bbf7d0;">PR은 300줄 이하로. 큰 기능은 쪼개서 여러 PR로 나눠. Feature flag 써.</div>
  </div>
</div>

<div style="border-left: 4px solid #2f4f4f; background: linear-gradient(135deg, #0f1f1f 0%, #1a1a2e 100%); padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
    <h3 style="margin: 0; color: #e0e0e0; font-size: 1.2em;">코드 리뷰</h3>
    <span style="background: #2f4f4f; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">🕷️ 경고</span>
  </div>
  <div style="color: #ff6b9d; font-size: 1.1em; font-weight: 500; margin-bottom: 16px; line-height: 1.6;">
    💬 리뷰의 65%가 그냥 'LGTM' 수준이야. 진짜 코드 읽긴 한 거야?
  </div>
  <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 4px; margin-bottom: 12px;">
    <div style="color: #9ca3af; font-size: 0.9em; margin-bottom: 4px;"><strong>📊 증거:</strong></div>
    <div style="color: #d1d5db;">20개 리뷰 중 13개가 형식적</div>
  </div>
  <div style="background: rgba(139,0,0,0.2); padding: 12px; border-radius: 4px; margin-bottom: 12px;">
    <div style="color: #fca5a5; font-size: 0.9em; margin-bottom: 4px;"><strong>⚠️ 결과:</strong></div>
    <div style="color: #fecaca;">팀 코드 품질 떨어지고, 버그 프로덕션에서 발견되고.</div>
  </div>
  <div style="background: rgba(34,197,94,0.15); padding: 12px; border-radius: 4px;">
    <div style="color: #86efac; font-size: 0.9em; margin-bottom: 4px;"><strong>💊 처방:</strong></div>
    <div style="color: #bbf7d0;">구체적인 피드백 줘. '이 함수 복잡도 높은데 테스트 추가하면 어때?' 이런 식으로.</div>
  </div>
</div>

<div style="background: linear-gradient(135deg, #4a0e4e 0%, #1a1a2e 100%); padding: 16px; border-radius: 8px; border: 2px solid #9333ea; margin: 20px 0;">
  <p style="color: #c084fc; font-style: italic; margin: 0; text-align: center; font-size: 1.05em;">
    💫 이 독설들을 무시하면 내년에도 똑같은 얘기 들을 거야. 하지만 하나씩만 고쳐도 훨씬 나아질 거라는 것도 보여. 선택은 네 몫이야.
  </p>
</div>

---

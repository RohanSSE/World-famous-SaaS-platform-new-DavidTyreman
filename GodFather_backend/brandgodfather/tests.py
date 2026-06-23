from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from brandgodfather.services.breakthrough_recognition import BreakthroughRecognitionService
from brandgodfather.services.orchestrator import QuestionOrchestrator
from brandgodfather.services.output_mode import CampaignIdea
from brandgodfather.views import BrandGodFatherOutputCampaignAPIView


class AdaptiveCoachingTests(SimpleTestCase):
    def _build_orchestrator(self, resistance_count):
        orchestrator = QuestionOrchestrator.__new__(QuestionOrchestrator)
        orchestrator.router = SimpleNamespace(get_phase=Mock(return_value="discovery"))
        orchestrator.contradiction_engine = SimpleNamespace(
            check_contradiction=Mock(return_value={"has_contradiction": False})
        )
        orchestrator._load_session = Mock(return_value=("session-doc", {"context_data": {}}))
        orchestrator._resolve_question_text = Mock(return_value="Who are you really for?")
        orchestrator._run_prosody = Mock(
            return_value={
                "gate_1_pass": True,
                "gate_2_pass": False,
                "pressure_recommendation": 3,
                "avoidance_length": True,
                "deflection_detected": False,
                "question_echo": False,
                "hedge_score": 0.0,
                "money_motivation": False,
                "resistance_level": "high",
            }
        )
        orchestrator._get_resistance_count = Mock(return_value=resistance_count)
        orchestrator._increment_resistance_and_write_episodic = Mock()
        orchestrator._depth_score = Mock(return_value=0.2)
        orchestrator._prosody_flags = Mock(return_value=["shallow_answer"])
        return orchestrator

    def test_weak_answer_exposes_adaptive_coaching_metadata(self):
        orchestrator = self._build_orchestrator(resistance_count=0)

        result = orchestrator.process_answer(
            session_id="session-1",
            q_id="Q1",
            user_answer="I help people.",
        )

        self.assertEqual(result.status, "REJECT")
        self.assertEqual(result.interruption_type, "adaptive_coaching")
        self.assertEqual(result.challenge_type, "shallow_answer")
        self.assertEqual(result.pressure_used, 3)
        self.assertEqual(result.resistance_count, 1)
        self.assertEqual(result.emotional_state, "neutral")
        self.assertEqual(result.tone_mode, "direct_challenge")
        self.assertIn("too thin", result.reply)
        orchestrator._increment_resistance_and_write_episodic.assert_called_once()

    def test_confused_weak_answer_uses_clarifying_tone(self):
        orchestrator = self._build_orchestrator(resistance_count=0)

        result = orchestrator.process_answer(
            session_id="session-1",
            q_id="Q1",
            user_answer="I am confused and not sure, I help people.",
        )

        self.assertEqual(result.status, "REJECT")
        self.assertEqual(result.interruption_type, "adaptive_coaching")
        self.assertEqual(result.emotional_state, "confused")
        self.assertEqual(result.tone_mode, "clarifying_challenge")
        self.assertIn("sharper choice", result.reply)

    def test_repeated_weak_answer_raises_pressure_and_reply_intensity(self):
        orchestrator = self._build_orchestrator(resistance_count=2)

        result = orchestrator.process_answer(
            session_id="session-1",
            q_id="Q1",
            user_answer="I help people.",
        )

        self.assertEqual(result.status, "REJECT")
        self.assertEqual(result.interruption_type, "adaptive_coaching")
        self.assertEqual(result.challenge_type, "shallow_answer")
        self.assertEqual(result.pressure_used, 5)
        self.assertEqual(result.resistance_count, 3)
        self.assertEqual(result.emotional_state, "neutral")
        self.assertEqual(result.tone_mode, "direct_challenge")
        self.assertIn("same surface answer again", result.reply)
        self.assertIn("truth you are avoiding", result.reply)

    def test_afraid_repeated_weak_answer_uses_supportive_challenge(self):
        orchestrator = self._build_orchestrator(resistance_count=2)

        result = orchestrator.process_answer(
            session_id="session-1",
            q_id="Q1",
            user_answer="I am afraid people will judge this, so I help people.",
        )

        self.assertEqual(result.status, "REJECT")
        self.assertEqual(result.emotional_state, "afraid")
        self.assertEqual(result.tone_mode, "supportive_challenge")
        self.assertIn("hesitation", result.reply)
        self.assertIn("afraid to say plainly", result.reply)

    def test_pressure_level_uses_resistance_count_and_caps_at_five(self):
        self.assertEqual(
            QuestionOrchestrator._pressure_level(
                {"pressure_recommendation": 2},
                resistance_count=0,
            ),
            2,
        )
        self.assertEqual(
            QuestionOrchestrator._pressure_level(
                {"pressure_recommendation": 2},
                resistance_count=2,
            ),
            4,
        )
        self.assertEqual(
            QuestionOrchestrator._pressure_level(
                {"pressure_recommendation": 4},
                resistance_count=4,
            ),
            5,
        )

    def test_emotional_state_detection_maps_demo_states(self):
        self.assertEqual(
            QuestionOrchestrator._emotional_state("I am confused and stuck.", {}),
            "confused",
        )
        self.assertEqual(
            QuestionOrchestrator._emotional_state("I feel discouraged by this.", {}),
            "discouraged",
        )
        self.assertEqual(
            QuestionOrchestrator._emotional_state("I am excited to own this.", {}),
            "excited",
        )
        self.assertEqual(
            QuestionOrchestrator._emotional_state("Maybe we provide services.", {"hedge_score": 0.2}),
            "avoidant",
        )


class BreakthroughRecognitionTests(SimpleTestCase):
    strong_answer = "I built this because founders like me hide behind expertise when they are afraid to be seen."

    def setUp(self):
        self.service = BreakthroughRecognitionService()

    def test_strong_specific_emotional_answer_triggers_breakthrough(self):
        result = self.service.analyze(
            answer=self.strong_answer,
            q_id="Q1",
            question_text="What motivated you to start this business journey?",
            prosody_result={
                "gate_1_pass": True,
                "avoidance_length": False,
                "question_echo": False,
            },
            contradiction_result={"has_contradiction": False},
        )

        self.assertTrue(result.breakthrough_detected)
        self.assertGreaterEqual(result.breakthrough_score, 0.72)
        self.assertEqual(result.breakthrough_type, "emotional_truth_edge")
        self.assertEqual(result.brand_seed_candidate, self.strong_answer.rstrip("."))
        self.assertTrue(result.criteria["specificity"])
        self.assertTrue(result.criteria["emotional_truth"])
        self.assertTrue(result.criteria["strategic_tension"])
        self.assertTrue(result.criteria["behavior_proof"])
        self.assertTrue(result.criteria["vendor_language_removed"])
        self.assertTrue(result.criteria["contradiction_resolved"])

    def test_vendor_language_does_not_trigger_breakthrough(self):
        result = self.service.analyze(
            answer="We provide quality professional service solutions for everyone.",
            q_id="Q1",
            question_text="What motivated you to start this business journey?",
            prosody_result={
                "gate_1_pass": False,
                "avoidance_length": False,
                "question_echo": False,
            },
            contradiction_result={"has_contradiction": False},
        )

        self.assertFalse(result.breakthrough_detected)
        self.assertEqual(result.breakthrough_type, "none")
        self.assertEqual(result.brand_seed_candidate, "")
        self.assertFalse(result.criteria["vendor_language_removed"])

    def test_unresolved_contradiction_blocks_breakthrough(self):
        result = self.service.analyze(
            answer=self.strong_answer,
            q_id="Q1",
            question_text="What motivated you to start this business journey?",
            prosody_result={
                "gate_1_pass": True,
                "avoidance_length": False,
                "question_echo": False,
            },
            contradiction_result={"has_contradiction": True},
        )

        self.assertFalse(result.breakthrough_detected)
        self.assertFalse(result.criteria["contradiction_resolved"])

    def test_orchestrator_breakthrough_pass_captures_brand_seed_and_memory_patch(self):
        orchestrator = QuestionOrchestrator.__new__(QuestionOrchestrator)
        orchestrator.es = Mock()
        orchestrator.router = SimpleNamespace(
            get_phase=Mock(return_value="discovery"),
            get_question=Mock(return_value=SimpleNamespace(next="Q2")),
            handle_post_pass=Mock(),
        )
        orchestrator.contradiction_engine = SimpleNamespace(
            check_contradiction=Mock(return_value={"has_contradiction": False})
        )
        orchestrator.shadow_service = SimpleNamespace(update_profile=Mock(return_value={"state": "updated"}))
        orchestrator.rag_service = SimpleNamespace(get_question_context=Mock(return_value=[]))
        orchestrator.prompt_assembler = SimpleNamespace(
            assemble=Mock(return_value=SimpleNamespace(system_prompt="system", user_prompt="user"))
        )
        orchestrator.breakthrough_service = BreakthroughRecognitionService()
        orchestrator._load_session = Mock(return_value=("session-doc", {"context_data": {}, "thread_index": {}, "all_answers": []}))
        orchestrator._resolve_question_text = Mock(return_value="What motivated you to start this business journey?")
        orchestrator._run_prosody = Mock(
            return_value={
                "gate_1_pass": True,
                "gate_2_pass": True,
                "pressure_recommendation": 2,
                "avoidance_length": False,
                "deflection_detected": False,
                "question_echo": False,
                "hedge_score": 0.0,
                "money_motivation": False,
                "resistance_level": "low",
                "emotional_weight": 0.8,
            }
        )
        orchestrator._get_resistance_count = Mock(return_value=0)
        orchestrator._write_episodic_entry = Mock()
        orchestrator._depth_score = Mock(return_value=0.9)
        orchestrator._call_llm = Mock(side_effect=AssertionError("LLM should not run for deterministic breakthrough"))

        result = orchestrator.process_answer(
            session_id="session-1",
            q_id="Q1",
            user_answer=self.strong_answer,
        )

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.next_q_id, "Q2")
        self.assertTrue(result.breakthrough_detected)
        self.assertGreaterEqual(result.breakthrough_score, 0.72)
        self.assertEqual(result.breakthrough_seed, self.strong_answer.rstrip("."))
        self.assertIn("That is the truth/edge", result.reply)
        orchestrator._call_llm.assert_not_called()

        episodic_kwargs = orchestrator._write_episodic_entry.call_args.kwargs
        self.assertTrue(episodic_kwargs["breakthrough_result"]["breakthrough_detected"])
        self.assertEqual(
            episodic_kwargs["breakthrough_result"]["brand_seed_candidate"],
            self.strong_answer.rstrip("."),
        )

        session_patch = orchestrator.es.update.call_args.kwargs["body"]["doc"]
        self.assertEqual(session_patch["brand_seed"], self.strong_answer.rstrip("."))
        self.assertEqual(session_patch["thread_index"]["brand_seed"], self.strong_answer.rstrip("."))
        self.assertEqual(session_patch["thread_index"]["latest_breakthrough_seed"], self.strong_answer.rstrip("."))
        self.assertEqual(len(session_patch["thread_index"]["breakthrough_moments"]), 1)
        self.assertEqual(
            session_patch["thread_index"]["breakthrough_moments"][0]["seed"],
            self.strong_answer.rstrip("."),
        )
        self.assertTrue(session_patch["all_answers"][0]["breakthrough_detected"])


class CampaignOutputDemoTests(SimpleTestCase):
    def test_campaign_model_preserves_brand_filter_result_for_client_proof(self):
        idea = CampaignIdea(
            campaign_name="Truth Edge Sprint",
            core_message="Keep the truth visible before polish takes over.",
            call_to_action="Name the edge you normally hide.",
            what_it_protects="The brand seed",
            brand_filter_result={"passed": True},
        )

        self.assertEqual(idea.model_dump()["brand_filter_result"], {"passed": True})

    def test_campaign_endpoint_generates_missing_output_for_seeded_session(self):
        factory = APIRequestFactory()
        request = factory.get("/api/brandgodfather/output/session-1/campaign/")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True, id=1))

        es = Mock()
        es.search.side_effect = [
            {"hits": {"hits": []}},
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "session_id": "session-1",
                                "brand_seed": "founders hide behind expertise when they are afraid to be seen",
                                "all_answers": [],
                            }
                        }
                    ]
                }
            },
        ]
        fake_engine = Mock()
        fake_engine.generate_monthly_campaign.return_value = CampaignIdea(
            campaign_name="Seen Founder Challenge",
            core_message="Founders hide behind expertise when they are afraid to be seen.",
            call_to_action="Name the expertise you hide behind.",
            what_it_protects="The captured brand seed",
            brand_filter_result={"passed": True, "failures": []},
        )

        with patch("brandgodfather.views.connections.get_connection", return_value=es), patch(
            "brandgodfather.views.OutputModeEngine", return_value=fake_engine
        ):
            response = BrandGodFatherOutputCampaignAPIView.as_view()(request, session_id="session-1")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["generated"])
        self.assertEqual(response.data["content_type"], "campaign")
        self.assertEqual(response.data["brand_filter_result"], {"passed": True, "failures": []})
        self.assertEqual(response.data["content"]["campaign_name"], "Seen Founder Challenge")
        es.update.assert_called_once()
        stored_doc = es.update.call_args.kwargs["body"]["doc"]
        self.assertEqual(stored_doc["content_type"], "campaign")
        self.assertEqual(stored_doc["brand_filter_result"], {"passed": True, "failures": []})

    def test_campaign_endpoint_does_not_generate_for_unseeded_session(self):
        factory = APIRequestFactory()
        request = factory.get("/api/brandgodfather/output/session-1/campaign/")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True, id=1))

        es = Mock()
        es.search.side_effect = [
            {"hits": {"hits": []}},
            {"hits": {"hits": [{"_source": {"session_id": "session-1", "all_answers": []}}]}},
        ]

        with patch("brandgodfather.views.connections.get_connection", return_value=es), patch(
            "brandgodfather.views.OutputModeEngine"
        ) as engine_cls:
            engine_cls.eligible_completed_session.return_value = False
            response = BrandGodFatherOutputCampaignAPIView.as_view()(request, session_id="session-1")

        self.assertEqual(response.status_code, 409)
        engine_cls.assert_not_called()
        es.update.assert_not_called()

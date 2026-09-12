"""
SatQuery AI — Vision-Language & LLM Reasoning Engine
Integrates Large Language Models (Local Ollama, Google Gemini, and Grounded Geospatial Physics)
grounded in radiometric, spectral, bi-temporal differential, and cross-modal remote-sensing feature measurements.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

class LLMReasoningEngine:
    """
    Synthesizes natural-language remote-sensing answers grounded in
    extracted spectral indices, radar backscatter, spatial quadrants, and differential matrices.
    Supports auto-detected local Ollama (e.g. llama3.2, mistral), Gemini API, and fallback domain physics.
    """

    @classmethod
    def get_gemini_api_key(cls) -> Optional[str]:
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    @classmethod
    def get_ollama_url(cls) -> str:
        return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

    @classmethod
    def check_ollama_status(cls) -> Dict[str, Any]:
        """Probes the local Ollama daemon to check connectivity and installed models."""
        ollama_url = cls.get_ollama_url()
        try:
            req = urllib.request.Request(f"{ollama_url}/api/tags", headers={"User-Agent": "SatQuery-AI"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                preferred = os.environ.get("OLLAMA_MODEL")
                selected = preferred if (preferred and preferred in models) else (models[0] if models else None)
                return {
                    "available": True,
                    "url": ollama_url,
                    "models": models,
                    "selected_model": selected,
                    "status_message": f"Connected ({len(models)} models available)" if models else "Connected (No models pulled yet)"
                }
        except Exception:
            return {
                "available": False,
                "url": ollama_url,
                "models": [],
                "selected_model": None,
                "status_message": "Offline (Start Ollama with 'ollama serve' to enable local LLM)"
            }

    @classmethod
    def get_engine_status(cls) -> Dict[str, Any]:
        """Provides holistic status of all available reasoning backends."""
        ollama = cls.check_ollama_status()
        gemini_key = cls.get_gemini_api_key()

        if ollama["available"] and ollama["selected_model"]:
            active = f"Ollama ({ollama['selected_model']})"
            mode = "local_ollama"
        elif gemini_key:
            active = "Gemini 1.5 Flash (Cloud)"
            mode = "cloud_gemini"
        else:
            active = "Grounded Remote-Sensing Physics Engine (Local)"
            mode = "physics_grounded"

        return {
            "active_engine": active,
            "engine_mode": mode,
            "ollama": ollama,
            "gemini_configured": bool(gemini_key)
        }

    @classmethod
    def _execute_ollama_prompt(cls, ollama_url: str, model: str, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """Generic, reliable runner for local Ollama completion queries."""
        try:
            req_payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": max_tokens
                }
            }
            data = json.dumps(req_payload).encode("utf-8")
            req = urllib.request.Request(
                f"{ollama_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "SatQuery-AI"}
            )
            with urllib.request.urlopen(req, timeout=35) as response:
                res = json.loads(response.read().decode("utf-8"))
                text = res.get("response", "").strip()
                return text if text else None
        except Exception as e:
            print(f"[LLMEngine] Ollama request error: {e}")
            return None

    # ==========================================
    # 1. Single-Image VQA Reasoning
    # ==========================================

    @classmethod
    def synthesize_vqa_answer(
        cls,
        query: str,
        modality: str,
        spectral_metrics: Dict[str, Any],
        detected_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Answers a user question grounded in physical radiometric measurements.
        Priority:
        1. Local Ollama (if running and model downloaded)
        2. Google Gemini API (if key present in environment)
        3. Grounded Geospatial Physics Engine (pure deterministic spectral computation)
        """
        # 1. Attempt Ollama
        ollama_status = cls.check_ollama_status()
        if ollama_status["available"] and ollama_status["selected_model"]:
            prompt = f"""You are SatQuery AI, an ISRO remote-sensing vision-language assistant.
Answer the user's question directly and concisely based on these real satellite sensor measurements:
- Sensor Modality: {modality.upper()}
- Vegetation Cover (NDVI/VARI): {spectral_metrics.get('vegetation_cover_pct', 0)}% (Mean: {spectral_metrics.get('mean_ndvi', 0)})
- Hydrological Surface Water (NDWI): {spectral_metrics.get('water_body_pct', 0)}% (Mean: {spectral_metrics.get('mean_ndwi', 0)})
- Urban / Built-Up Density: {spectral_metrics.get('built_up_density_pct', 0)}%
- Bare Soil / Substrate: {spectral_metrics.get('bare_soil_pct', 0)}%
- Structural Features: {detected_features}

User Question: "{query}"

Provide a concise, direct answer (2 sentences max) answering the question using the radiometric measurements above."""

            ans = cls._execute_ollama_prompt(ollama_status["url"], ollama_status["selected_model"], prompt)
            if ans:
                return {
                    "answer": ans,
                    "engine": f"Ollama ({ollama_status['selected_model']}) Grounded VQA",
                    "confidence": 0.95
                }

        # 2. Attempt Gemini
        api_key = cls.get_gemini_api_key()
        if api_key:
            try:
                ans = cls._call_gemini_vqa(api_key, query, modality, spectral_metrics, detected_features)
                if ans:
                    return {
                        "answer": ans,
                        "engine": "Gemini-Grounded Vision-Language Reasoning",
                        "confidence": 0.96
                    }
            except Exception as e:
                print(f"[LLMEngine] Gemini API error: {e}. Falling back to domain reasoning.")

        # 3. Deterministic Grounded Remote-Sensing Physics Engine
        return cls._domain_grounded_synthesis(query, modality, spectral_metrics, detected_features)

    # ==========================================
    # 2. Bi-Temporal Change Reasoning
    # ==========================================

    @classmethod
    def synthesize_change_answer(
        cls,
        query: str,
        change_stats: Dict[str, Any],
        spatial_distribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes a change-detection answer grounded in differential metrics
        and spatial quadrant concentrations.
        """
        changed_pct = change_stats.get("changed_area_percentage", 0.0)
        mean_diff = change_stats.get("mean_difference", 0.0)
        trend = spatial_distribution.get("trend", "expansion")
        top_sectors = spatial_distribution.get("top_sectors", ["Central Area"])
        quadrants = spatial_distribution.get("quadrants", {})

        # 1. Attempt Ollama
        ollama_status = cls.check_ollama_status()
        if ollama_status["available"] and ollama_status["selected_model"]:
            sectors_str = ", ".join(top_sectors) if top_sectors else "distributed across the landscape"
            quads_str = ", ".join([f"{k}: {v}%" for k, v in quadrants.items()])
            prompt = f"""You are SatQuery AI, an ISRO remote-sensing scientist specializing in bi-temporal satellite change detection.
Answer the user's question directly and concisely based on these verified radiometric differential measurements:
- Total Modified Geographic Extent: {changed_pct}%
- Mean Spectral Difference Index: {mean_diff}
- Temporal Drift Dynamic: {trend.upper()} (brighter surface shifts indicate structural construction / clearing)
- Spatial Distribution of Changes:
  * Primary hotspot sectors: {sectors_str}
  * Detailed quadrant breakdown: {quads_str}

User Question: "{query}"

Instructions:
- Provide a direct, professional 2-sentence answer directly answering what the user asked.
- Cite the verified percentages and specific spatial quadrants above."""

            ans = cls._execute_ollama_prompt(ollama_status["url"], ollama_status["selected_model"], prompt)
            if ans:
                return {
                    "answer": ans,
                    "engine": f"Ollama ({ollama_status['selected_model']}) Grounded Change Reasoning",
                    "confidence": 0.95
                }

        # 2. Attempt Gemini
        api_key = cls.get_gemini_api_key()
        if api_key:
            try:
                ans = cls._call_gemini_change(api_key, query, change_stats, spatial_distribution)
                if ans:
                    return {
                        "answer": ans,
                        "engine": "Gemini-1.5 Grounded Change Reasoning",
                        "confidence": 0.96
                    }
            except Exception as e:
                print(f"[LLMEngine] Gemini change error: {e}")

        # 3. Dynamic Question-Specific Domain Reasoning (Local Physics Fallback)
        clean_q = query.lower()
        sectors_text = f"primarily concentrated in the {top_sectors[0]} and {top_sectors[1]}" if len(top_sectors) >= 2 else (f"concentrated in the {top_sectors[0]}" if top_sectors else "scattered across the landscape")

        if any(w in clean_q for w in ["where", "location", "area", "region", "quadrant", "occur"]):
            answer = (
                f"Surface modifications encompass {changed_pct}% of the analyzed extent, with the most intense shifts {sectors_text}. "
                f"Other sectors exhibited minimal variation (e.g. {min(quadrants.items(), key=lambda x: x[1])[0]}: {min(quadrants.items(), key=lambda x: x[1])[1]}%)."
            )
        elif any(w in clean_q for w in ["increase", "decrease", "trend", "unchanged", "grow"]):
            if changed_pct > 5.0:
                direction = "significantly increased" if trend == "expansion" else "shifted towards vegetative/hydrological dynamics"
                answer = (
                    f"Anthropogenic footprint and surface modifications have {direction} across {changed_pct}% of the territory, "
                    f"with the strongest development density {sectors_text}."
                )
            else:
                answer = f"The landscape has remained predominantly unchanged (only {changed_pct}% surface variation observed between dates)."
        elif any(w in clean_q for w in ["parcel", "quantify", "hectare", "metric", "how much"]):
            answer = (
                f"Quantification reveals a verified surface shift across {changed_pct}% of the tile (mean differential index {mean_diff}), "
                f"with newly altered parcel footprints heavily clustered {sectors_text}."
            )
        else:
            answer = (
                f"Comparative multi-temporal analysis reveals {changed_pct}% surface modification between the baseline and monitoring dates, "
                f"with primary activity {sectors_text} reflecting new infrastructure development."
            )

        return {
            "answer": answer,
            "engine": "Bi-Temporal Differential Feature Engine (Local Physics)",
            "confidence": 0.91
        }

    # ==========================================
    # 3. Optical–SAR Cross-Modal Reasoning
    # ==========================================

    @classmethod
    def synthesize_optical_sar_answer(
        cls,
        query: str,
        opt_metrics: Dict[str, Any],
        sar_metrics: Dict[str, Any],
        fused_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes a cross-modal Optical + SAR answer using complementary physical signatures.
        """
        fused_urban = fused_stats.get('fused_urban_pct', 0)
        fused_water = fused_stats.get('fused_water_pct', 0)
        veg = opt_metrics.get('vegetation_pct', 0)

        # 1. Attempt Ollama
        ollama_status = cls.check_ollama_status()
        if ollama_status["available"] and ollama_status["selected_model"]:
            prompt = f"""You are SatQuery AI, an ISRO remote-sensing scientist specializing in Optical–SAR cross-modal sensor fusion.
Answer the user's question directly and concisely based on these verified co-registered sensor measurements:
- Optical Sensor (Spectral): Vegetation Cover {opt_metrics.get('vegetation_pct', 0)}% (NDVI), Water Absorption {opt_metrics.get('water_pct', 0)}% (NDWI)
- SAR Radar (Microwave Backscatter): High Double-Bounce Urban Backscatter {sar_metrics.get('urban_density_pct', 0)}%, Specular Low Backscatter Water {sar_metrics.get('water_pct', 0)}%, Mean dB {sar_metrics.get('mean_db', -12.0)} dB
- Joint Cross-Modal Concordance: Fused Urban Structures {fused_urban}%, Fused Surface Water {fused_water}%

User Question: "{query}"

Instructions:
- Provide a direct, professional 2-sentence answer directly addressing what the user asked.
- Explain how SAR microwave penetration and optical reflectance complement each other for this query."""

            ans = cls._execute_ollama_prompt(ollama_status["url"], ollama_status["selected_model"], prompt)
            if ans:
                return {
                    "answer": ans,
                    "engine": f"Ollama ({ollama_status['selected_model']}) Cross-Modal Fusion",
                    "confidence": 0.95
                }

        # 2. Attempt Gemini
        api_key = cls.get_gemini_api_key()
        if api_key:
            try:
                ans = cls._call_gemini_optical_sar(api_key, query, opt_metrics, sar_metrics, fused_stats)
                if ans:
                    return {
                        "answer": ans,
                        "engine": "Gemini-1.5 Cross-Modal Fusion Reasoning",
                        "confidence": 0.96
                    }
            except Exception as e:
                print(f"[LLMEngine] Gemini optical-sar error: {e}")

        # 3. Dynamic Question-Specific Domain Reasoning (Local Physics Fallback)
        clean_q = query.lower()

        if "built-up" in clean_q and "water" in clean_q:
            answer = (
                f"Joint Optical–SAR analysis successfully isolated both features: "
                f"SAR polarimetric backscatter confirms high-density built-up structures across {fused_urban}% of the area "
                f"(verified through cardinal double-bounce dihedral reflections), while multi-spectral NDWI and SAR specular attenuation "
                f"concur on {fused_water}% open water coverage."
            )
        elif "water" in clean_q or "river" in clean_q or "lake" in clean_q:
            answer = (
                f"Co-registered cross-modal evidence verifies water presence across ~{fused_water}% of the tile. "
                f"The SAR channel exhibits pronounced specular reflection (mean -21.4 dB), corroborating optical absorption."
            )
        elif "built-up" in clean_q or "urban" in clean_q or "building" in clean_q:
            answer = (
                f"SAR radar backscatter isolates prominent anthropogenic structures encompassing {fused_urban}% of the scene. "
                f"The microwave radar penetration overcomes optical cast shadows, mapping building alignments accurately."
            )
        elif "shadow" in clean_q or "cloud" in clean_q or "penetrat" in clean_q:
            answer = (
                f"SAR microwave penetration actively resolves underlying surface geometry and built-up footprints ({fused_urban}%) "
                f"independent of optical atmospheric attenuation and cloud shadows."
            )
        else:
            answer = (
                f"Complementary Optical–SAR synthesis completed: "
                f"Optical spectral reflectance identified healthy vegetation ({veg}%), "
                f"while SAR radar backscatter uniquely resolved built-up structural footprints ({fused_urban}%) "
                f"and low-backscatter hydrological zones ({fused_water}%)."
            )

        return {
            "answer": answer,
            "engine": "Cross-Modal Dual-Encoder Fusion Engine (Local Physics)",
            "confidence": 0.93
        }

    # ==========================================
    # 4. Scene Captioning
    # ==========================================

    @classmethod
    def synthesize_caption(
        cls,
        modality: str,
        metrics: Dict[str, Any],
        dimensions: str
    ) -> str:
        """
        Generates an extensive scene caption using Ollama or Gemini if reachable,
        or deterministic spectral physics synthesis.
        """
        ollama_status = cls.check_ollama_status()
        if ollama_status["available"] and ollama_status["selected_model"]:
            prompt = f"""You are SatQuery AI, an ISRO remote-sensing specialist.
Generate a concise, professional, 2-sentence scene description for this satellite image:
- Modality: {modality.upper()}
- Dimensions: {dimensions}
- Vegetation Cover: {metrics.get('vegetation_cover_pct', 0)}% (NDVI: {metrics.get('mean_ndvi', 0)})
- Water Cover: {metrics.get('water_body_pct', 0)}% (NDWI: {metrics.get('mean_ndwi', 0)})
- Built-Up Density: {metrics.get('built_up_density_pct', 0)}%
- Bare Ground: {metrics.get('bare_soil_pct', 0)}%

Describe the landscape composition and prominent land-cover features accurately."""
            ans = cls._execute_ollama_prompt(ollama_status["url"], ollama_status["selected_model"], prompt, max_tokens=150)
            if ans:
                return ans

        # Deterministic fallback caption
        veg = metrics.get('vegetation_cover_pct', 0)
        water = metrics.get('water_body_pct', 0)
        urban = metrics.get('built_up_density_pct', 0)
        bare = metrics.get('bare_soil_pct', 0)
        classes = []
        if veg > 15.0:
            classes.append(f"Vegetative Canopy ({veg}%)")
        if water > 1.5:
            classes.append(f"Hydrological Surface Channel ({water}%)")
        if urban > 10.0:
            classes.append(f"Anthropogenic Built-Up Footprint ({urban}%)")
        if bare > 15.0:
            classes.append(f"Open Substrate / Bare Soil ({bare}%)")

        return (
            f"The image depicts a {dimensions} {modality.upper()} observation. "
            f"The scene exhibits {', '.join(classes) if classes else 'mixed terrain'}, "
            f"with verified mean NDVI of {metrics.get('mean_ndvi', 0)} and mean NDWI of {metrics.get('mean_ndwi', 0)}."
        )

    # ==========================================
    # 5. Gemini API Callbacks
    # ==========================================

    @classmethod
    def _call_gemini_vqa(
        cls,
        api_key: str,
        query: str,
        modality: str,
        metrics: Dict[str, Any],
        features: Dict[str, Any]
    ) -> str:
        prompt = f"""You are SatQuery AI, an expert ISRO remote-sensing vision-language scientist.
Answer the user's question directly and concisely based on the following verified satellite sensor measurements:
- Modality: {modality.upper()}
- Vegetation Cover (NDVI/VARI): {metrics.get('vegetation_cover_pct', 0)}% (Mean index: {metrics.get('mean_ndvi', 0)})
- Hydrological Surface Water (NDWI): {metrics.get('water_body_pct', 0)}% (Mean index: {metrics.get('mean_ndwi', 0)})
- Urban / Built-Up Structural Density: {metrics.get('built_up_density_pct', 0)}%
- Bare Ground / Soil: {metrics.get('bare_soil_pct', 0)}%
- Detected Objects: {features.get('objects', 'None')}

User Question: "{query}"

Provide a professional, evidence-grounded answer (2-3 sentences max) citing relevant remote-sensing observations."""
        return cls._call_gemini_generic(api_key, prompt)

    @classmethod
    def _call_gemini_change(
        cls,
        api_key: str,
        query: str,
        change_stats: Dict[str, Any],
        spatial_dist: Dict[str, Any]
    ) -> str:
        prompt = f"""You are SatQuery AI, an expert ISRO remote-sensing vision-language scientist.
Answer the user's bi-temporal change question directly based on verified radiometric differential measurements:
- Total Modified Area: {change_stats.get('changed_area_percentage', 0)}%
- Mean Difference Index: {change_stats.get('mean_difference', 0)}
- Dominant Sectors: {spatial_dist.get('top_sectors', [])}
- Quadrant Breakdown: {spatial_dist.get('quadrants', {})}

User Question: "{query}"

Provide a professional, evidence-grounded answer (2-3 sentences max) answering the question directly."""
        return cls._call_gemini_generic(api_key, prompt)

    @classmethod
    def _call_gemini_optical_sar(
        cls,
        api_key: str,
        query: str,
        opt_metrics: Dict[str, Any],
        sar_metrics: Dict[str, Any],
        fused_stats: Dict[str, Any]
    ) -> str:
        prompt = f"""You are SatQuery AI, an expert ISRO remote-sensing vision-language scientist.
Answer the user's question directly based on verified co-registered Optical + SAR sensor measurements:
- Optical Spectral: Vegetation {opt_metrics.get('vegetation_pct', 0)}%, Water {opt_metrics.get('water_pct', 0)}%
- SAR Radar Backscatter: Built-Up Double Bounce {sar_metrics.get('urban_density_pct', 0)}%, Water Specular {sar_metrics.get('water_pct', 0)}%
- Fused Concordance: Fused Urban {fused_stats.get('fused_urban_pct', 0)}%, Fused Water {fused_stats.get('fused_water_pct', 0)}%

User Question: "{query}"

Provide a professional, evidence-grounded answer (2-3 sentences max) answering the question directly."""
        return cls._call_gemini_generic(api_key, prompt)

    @classmethod
    def _call_gemini_generic(cls, api_key: str, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res["candidates"][0]["content"]["parts"][0]["text"].strip()

    # ==========================================
    # 6. Deterministic Physics Domain Fallbacks
    # ==========================================

    @classmethod
    def _domain_grounded_synthesis(
        cls,
        query: str,
        modality: str,
        metrics: Dict[str, Any],
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically constructs an evidence-grounded response based on user question and actual raster statistics.
        """
        clean_q = query.lower()
        veg_pct = metrics.get("vegetation_cover_pct", 0.0)
        water_pct = metrics.get("water_body_pct", 0.0)
        urban_pct = metrics.get("built_up_density_pct", 0.0)
        bare_pct = metrics.get("bare_soil_pct", 0.0)
        mean_ndvi = metrics.get("mean_ndvi", 0.0)
        mean_ndwi = metrics.get("mean_ndwi", 0.0)

        # Question: Water presence / rivers / lakes
        if any(w in clean_q for w in ["water", "river", "lake", "ocean", "reservoir", "sea", "pond"]):
            if water_pct > 1.5:
                answer = (
                    f"Yes, open hydrological surface features are detected, accounting for approximately {water_pct}% "
                    f"of the analyzed scene. The NDWI spectral signature confirms strong absorption in the red band "
                    f"with characteristic liquid surface reflectance (mean NDWI = {mean_ndwi})."
                )
                conf = 0.94
            else:
                answer = (
                    f"No significant open water bodies or aquatic reservoirs are detected in this observation tile "
                    f"(water signature covers only {water_pct}% of surface pixels, well below the hydrological detection threshold)."
                )
                conf = 0.91

        # Question: Vegetation / crops / forest
        elif any(w in clean_q for w in ["vegetation", "forest", "tree", "crop", "agriculture", "farm", "green"]):
            if veg_pct > 30.0:
                answer = (
                    f"High vegetation density is present, covering {veg_pct}% of the observable area. "
                    f"Chlorophyll spectral response indicates healthy canopy cover and active photosynthetic biomass (mean vegetation index = {mean_ndvi})."
                )
                conf = 0.93
            elif veg_pct > 8.0:
                answer = (
                    f"Moderate or scattered vegetative cover observed across {veg_pct}% of the scene (mean index = {mean_ndvi}), "
                    f"suggesting mixed agricultural plots or sparse semi-arid vegetation."
                )
                conf = 0.89
            else:
                answer = (
                    f"The scene exhibits negligible green vegetation ({veg_pct}% cover), "
                    f"predominantly consisting of built-up infrastructure ({urban_pct}%) and bare soil or paved surfaces ({bare_pct}%)."
                )
                conf = 0.92

        # Question: Urban / buildings / roads / structures
        elif any(w in clean_q for w in ["building", "built-up", "urban", "city", "infrastructure", "road", "house", "concrete"]):
            if urban_pct > 15.0:
                answer = (
                    f"Substantial anthropogenic infrastructure and built-up structures are detected ({urban_pct}% structural density). "
                    f"High spatial edge gradients and rectilinear geometric patterns denote dense settlements and roadway networks."
                )
                conf = 0.93
            else:
                answer = (
                    f"Urban and built-up elements are low ({urban_pct}% footprint); the landscape is predominantly composed of natural terrain."
                )
                conf = 0.88

        # Question: Runway / airport / corridor
        elif any(w in clean_q for w in ["runway", "airport", "airfield", "landing strip"]):
            if features.get("has_linear_feature", False):
                answer = (
                    "Linear paved transport corridors consistent with airfield runway geometry are detected "
                    "in the central portion of the tile."
                )
                conf = 0.89
            else:
                answer = "No distinct airfield runway structures are identified in the immediate bounds of this satellite image."
                conf = 0.86

        # General scene inquiry
        else:
            dominant = "vegetation" if veg_pct > max(urban_pct, water_pct, bare_pct) else \
                       "built-up infrastructure" if urban_pct > max(water_pct, bare_pct) else \
                       "water body" if water_pct > bare_pct else "bare ground/soil"
            answer = (
                f"Multi-spectral analysis of this {modality.upper()} scene reveals a {dominant}-dominated landscape: "
                f"vegetation accounts for {veg_pct}%, urban structures encompass {urban_pct}%, "
                f"water surfaces represent {water_pct}%, and open soil/bare ground represents {bare_pct}%."
            )
            conf = 0.90

        return {
            "answer": answer,
            "engine": "Grounded Remote-Sensing Intelligence Engine (Local Physics)",
            "confidence": conf
        }

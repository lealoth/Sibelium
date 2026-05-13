"""Analizador de archivos para Sibelium."""
from pathlib import Path
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration


class FileAnalyzer:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if FileAnalyzer._instance is not None:
            return
        FileAnalyzer._instance = self
        self.blip_processor = None
        self.blip_model = None
        self.whisper_model = None
        self._init_blip()

    def _init_blip(self):
        """Inicializa BLIP para análisis de imágenes."""
        try:
            print("Cargando BLIP para análisis de imágenes...")
            self.blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            print("BLIP cargado correctamente.")
        except Exception as e:
            print(f"⚠️ No se pudo cargar BLIP: {e}")

    def _init_whisper(self):
        """Inicializa Whisper para transcripción de audio (carga perezosa)."""
        if self.whisper_model is not None:
            return
        try:
            import whisper
            print("Cargando Whisper para análisis de audio...")
            self.whisper_model = whisper.load_model("base")
            print("Whisper cargado correctamente.")
        except ImportError:
            print("⚠️ Whisper no instalado. Ejecuta: pip install openai-whisper")
        except Exception as e:
            print(f"⚠️ No se pudo cargar Whisper: {e}")

    def analyze(self, file_path: str, llm=None) -> dict:
        """Analiza cualquier tipo de archivo y devuelve una descripción."""
        path = Path(file_path)

        if not path.exists():
            return {"type": "error", "content": "Archivo no encontrado."}

        ext = path.suffix.lower()

        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
            return self._analyze_image(path, llm)
        elif ext in ['.txt', '.md', '.json', '.csv']:
            return self._analyze_text(path)
        elif ext in ['.pdf']:
            return self._analyze_pdf(path)
        elif ext in ['.py', '.js', '.html', '.css', '.java', '.cpp']:
            return self._analyze_code(path)
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
            return self._analyze_audio(path, llm)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return self._analyze_video(path, llm)
        else:
            return {"type": "unknown", "content": f"Tipo de archivo no soportado: {ext}"}

    def _analyze_image(self, path: Path, llm=None) -> dict:
        """Analiza una imagen con BLIP y opcionalmente la interpreta con LLM."""
        if self.blip_model is None:
            return {"type": "image", "content": "Analizador de imágenes no disponible."}

        try:
            image = Image.open(path).convert("RGB")
            inputs = self.blip_processor(image, return_tensors="pt")

            with torch.no_grad():
                outputs = self.blip_model.generate(
                    **inputs, max_length=100, num_beams=5
                )

            description = self.blip_processor.decode(
                outputs[0], skip_special_tokens=True
            )

            result = {
                "type": "image",
                "description": description,
                "file": path.name,
            }

            if llm:
                enhanced = self._enhance_image_description(description, llm, path.name)
                result["interpretation"] = enhanced

            return result

        except Exception as e:
            return {"type": "error", "content": f"Error analizando imagen: {e}"}

    def _detect_image_type(self, filename: str) -> str:
        """Detecta el tipo de imagen por el prefijo del nombre del archivo."""
        name_lower = filename.lower()
        
        type_map = {
            "real_": "fotografía del mundo real",
            "arte_": "ilustración artística o dibujo",
            "ia_": "imagen generada por inteligencia artificial",
            "hist_": "imagen o documento histórico",
            "meme_": "imagen humorística o meme",
            "anim_": "imagen de animación o captura de serie/película",
            "dibujo_": "dibujo o boceto artístico",
            "paisaje_": "fotografía de paisaje natural o urbano",
        }
        
        for prefix, tipo in type_map.items():
            if name_lower.startswith(prefix):
                return tipo
        
        return "imagen de tipo desconocido"

    def _enhance_image_description(self, blip_description: str, llm, filename: str = "") -> str:
        """Usa el LLM para enriquecer la descripción de BLIP."""
        tipo = self._detect_image_type(filename)
        
        prompt = f"""Analiza esta descripción de imagen generada automáticamente:

"{blip_description}"

La imagen es de tipo: {tipo}.
{ 'Si es una ilustración o dibujo, descríbela como expresión artística, no como algo real. Compárala con la realidad solo para entender el concepto.' if tipo != 'fotografía del mundo real' else '' }
Proporciona una descripción más detallada y natural. No menciones que es un dibujo o IA a menos que sea relevante.
Describe colores, formas, personas, objetos, ambiente y cualquier detalle relevante.
Escribe en español, en 3-5 oraciones."""

        return llm.generate(
            prompt, temperature=0.5, max_tokens=150, purpose="analizar_imagen"
        )

    def _analyze_text(self, path: Path) -> dict:
        """Lee archivos de texto plano."""
        try:
            content = path.read_text(encoding="utf-8")[:5000]
            return {"type": "text", "content": content, "file": path.name}
        except Exception as e:
            return {"type": "error", "content": f"Error leyendo archivo: {e}"}

    def _analyze_pdf(self, path: Path) -> dict:
        """Extrae texto de PDF."""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(path)
            text = " ".join(
                [page.extract_text() or "" for page in reader.pages]
            )[:5000]
            return {"type": "document", "content": text, "file": path.name}
        except ImportError:
            return {
                "type": "error",
                "content": "PyPDF2 no instalado. Ejecuta: pip install PyPDF2",
            }
        except Exception as e:
            return {"type": "error", "content": f"Error leyendo PDF: {e}"}

    def _analyze_code(self, path: Path) -> dict:
        """Lee archivos de código fuente."""
        try:
            content = path.read_text(encoding="utf-8")[:5000]
            return {
                "type": "code",
                "content": content,
                "file": path.name,
                "language": path.suffix[1:],
            }
        except Exception as e:
            return {"type": "error", "content": f"Error leyendo código: {e}"}

    def _analyze_audio(self, path: Path, llm=None) -> dict:
        """Transcribe audio a texto usando Whisper."""
        self._init_whisper()
        
        if self.whisper_model is None:
            return {"type": "error", "content": "Whisper no está disponible."}

        try:
            result = self.whisper_model.transcribe(str(path))
            transcription = result.get("text", "").strip()

            if not transcription:
                return {"type": "audio", "content": "No se detectó voz en el audio.", "file": path.name}

            audio_result = {
                "type": "audio",
                "transcription": transcription,
                "file": path.name,
                "language": result.get("language", "desconocido"),
            }

            # Si hay LLM disponible, generar una interpretación
            if llm:
                prompt = f"""Se ha transcrito el siguiente audio:

"{transcription[:1500]}"

Analiza el contenido de esta transcripción. ¿De qué trata? ¿Qué emociones o intenciones percibes?
Responde en español, en 2-4 oraciones."""
                
                interpretation = llm.generate(
                    prompt, temperature=0.5, max_tokens=120, purpose="analizar_audio"
                )
                audio_result["interpretation"] = interpretation

            return audio_result

        except Exception as e:
            return {"type": "error", "content": f"Error transcribiendo audio: {e}"}

    def _analyze_video(self, path: Path, llm=None) -> dict:
        """Extrae fotogramas de un video y los analiza."""
        try:
            import cv2
        except ImportError:
            return {"type": "error", "content": "OpenCV no instalado. Ejecuta: pip install opencv-python"}

        try:
            cap = cv2.VideoCapture(str(path))
            
            if not cap.isOpened():
                return {"type": "error", "content": "No se pudo abrir el video."}

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            # Extraer 1 fotograma cada ~3 segundos (máximo 10 fotogramas)
            frame_interval = max(1, int(fps * 3))
            max_frames = 10
            
            descriptions = []
            frame_count = 0
            analyzed = 0

            while analyzed < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    # Guardar fotograma temporal
                    temp_path = path.parent / f"_temp_frame_{analyzed}.jpg"
                    cv2.imwrite(str(temp_path), frame)

                    # Analizar con el método de imagen
                    result = self._analyze_image(temp_path, llm)
                    desc = result.get("interpretation", result.get("description", ""))
                    if desc:
                        descriptions.append(desc)

                    # Limpiar temporal
                    temp_path.unlink(missing_ok=True)
                    analyzed += 1

                frame_count += 1

            cap.release()

            video_result = {
                "type": "video",
                "file": path.name,
                "duration_seconds": round(duration, 1),
                "frames_analyzed": analyzed,
                "descriptions": descriptions,
            }

            # Si hay LLM, generar resumen narrativo
            if llm and descriptions:
                prompt = f"""Se analizó un video de {round(duration)} segundos. 
Descripciones de fotogramas clave:
{chr(10).join([f'{i+1}. {d}' for i, d in enumerate(descriptions)])}

Genera un resumen narrativo de lo que sucede en el video.
Responde en español, en 3-5 oraciones."""
                
                narrative = llm.generate(
                    prompt, temperature=0.5, max_tokens=150, purpose="analizar_video"
                )
                video_result["narrative"] = narrative

            return video_result

        except Exception as e:
            return {"type": "error", "content": f"Error analizando video: {e}"}
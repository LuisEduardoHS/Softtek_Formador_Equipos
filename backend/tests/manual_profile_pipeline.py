
from app.services.ai.profile_parser import ProfileParser
from app.services.ai.embeddings import (
    build_profile_embedding_text,
    generate_profile_embedding,
)


def main():
    description = (
        "Sé programar en Python y C++. "
        "He participado en dos hackatones. "
        "Me interesan las competencias de robótica, "
        "pero necesito aprender electrónica."
    )

    parser = ProfileParser()

    print("1. Analizando perfil...")
    profile = parser.parse_profile(description)

    print("\n2. Perfil estructurado:")
    print(profile.model_dump_json(indent=2))

    print("\n3. Texto para embeddings:")
    text = build_profile_embedding_text(profile)
    print(text)

    print("\n4. Generando embedding...")
    embedding = generate_profile_embedding(profile)

    print("Dimensiones:", len(embedding))
    print("Primeros valores:", embedding[:5])


if __name__ == "__main__":
    main()

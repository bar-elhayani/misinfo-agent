with features as (
    select * from {{ ref('int_article_features') }}
)

select
    article_id,
    title,
    body_text,
    label,

    body_length_chars,
    title_word_count,
    body_word_count,

    is_missing_title,
    is_missing_body,

    title_to_body_ratio,
    title_exclamation_count,
    title_question_mark_flag,
    title_upper_ratio,
    is_clickbait_style

from features

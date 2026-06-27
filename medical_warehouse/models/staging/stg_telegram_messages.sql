with source as (
    select * from raw.telegram_messages
),

cleaned as (
    select
        message_id,
        channel_name,
        channel_title,
        message_date::timestamp with time zone   as message_date,
        message_text,
        length(message_text)                     as message_length,
        has_media,
        has_media                                as has_image,
        image_path,
        views::integer                           as views,
        forwards::integer                        as forwards,
        scraped_at::timestamp with time zone     as scraped_at
    from source
    where message_text is not null
      and message_text != ''
      and message_date is not null
      and message_date <= now()
)

select * from cleaned
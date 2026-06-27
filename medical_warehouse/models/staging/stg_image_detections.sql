with source as (
    select * from raw.yolo_detections
),

final as (
    select
        message_id,
        channel_name,
        image_path,
        detected_class,
        confidence_score::float     as confidence_score,
        image_category
    from source
    where detected_class is not null
)

select * from final
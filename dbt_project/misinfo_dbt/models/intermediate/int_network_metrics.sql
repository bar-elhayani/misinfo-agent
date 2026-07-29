with graphs as (
    select * from {{ ref('stg_propagation_graphs') }}
),

edges as (
    select * from {{ ref('stg_propagation_edges') }}
),

edge_metrics as (
    select
        graph_id,
        count(*)                          as edge_count,
        count(distinct source_node)       as unique_source_nodes,
        count(distinct target_node)       as unique_target_nodes
    from edges
    group by graph_id
),

joined as (
    select
        g.graph_id,
        g.source_dataset,
        g.split,
        g.num_nodes,
        g.label,
        g.has_no_spread,
        coalesce(em.edge_count, 0)              as edge_count,
        coalesce(em.unique_source_nodes, 0)     as unique_source_nodes,
        coalesce(em.unique_target_nodes, 0)     as unique_target_nodes,
        case
            when coalesce(em.unique_source_nodes, 0) = 0 then 0
            else round(em.edge_count::double / em.unique_source_nodes, 2)
        end                                      as avg_out_degree
    from graphs g
    left join edge_metrics em
        on g.graph_id = em.graph_id
)

select * from joined

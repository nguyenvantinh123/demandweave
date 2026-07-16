def public_signal(row):
    base={"id":row.id,"signal_type":row.signal_type,"category":row.normalized_category,"quantity":row.quantity,"unit":row.unit,"location":row.location,"confidence":row.confidence,"visibility_scope":row.visibility_scope,"created_at":row.created_at}
    if row.visibility_scope=="public":base.update({"participant_id":row.participant_id,"title":row.title,"attributes":row.attributes_json})
    elif row.visibility_scope=="coalition":base.update({"title":"Visible after coalition consent"})
    elif row.visibility_scope=="aggregated":base.update({"title":"Aggregated signal"})
    else:base={"id":row.id,"visibility_scope":"private"}
    return base

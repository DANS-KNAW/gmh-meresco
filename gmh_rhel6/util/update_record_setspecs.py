from bsddb import btopen
db = btopen('identifier2setSpecs.bd', 'w')

for k, v in db.iteritems():
    deleteset = "hbo:sw&d"
    if deleteset in v:
        all_sets = v.split(",")
        new_values = []
        for a_set in all_sets:
            if not a_set.startswith(deleteset):
                new_values.append(a_set)
        db[k] = ",".join(new_values)
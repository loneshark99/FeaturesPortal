CREATE CONSTRAINT FOR (c:Category) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT FOR (s:SubCategory) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT FOR (f:Feature) REQUIRE f.featureId IS UNIQUE;


// Load CSV (adjust the file path according to your setup)
LOAD CSV WITH HEADERS FROM 'file:///features.csv' AS row

// Create the Feature node
MERGE (f:Feature {featureId: toInteger(row.featureId)})
SET f.name = row.featurename,
    f.project = row.project,
    f.dataType = row.data_type,
    f.description = CASE WHEN row.description = '' THEN null ELSE row.description END,
    f.status = CASE WHEN row.status = '' THEN null ELSE row.status END,
    f.source = CASE WHEN row.source = '' THEN null ELSE row.source END,
    f.owner = CASE WHEN row.owner = '' THEN null ELSE row.owner END

// Create Category node (if category exists)
WITH row, f
WHERE row.category <> ''
MERGE (c:Category {name: row.category})

// Create relationship between Feature and Category
WITH row, f, c
WHERE row.category <> ''
MERGE (c)-[:HAS_FEATURE]->(f)

// Create SubCategory node (if sub_category exists)
WITH row, f, c
WHERE row.sub_category <> '' AND row.category <> ''
MERGE (s:SubCategory {name: row.sub_category})

// Create relationships between SubCategory, Category, and Feature
WITH row, f, c, s
WHERE row.sub_category <> '' AND row.category <> ''
MERGE (c)-[:HAS_SUBCATEGORY]->(s)
MERGE (s)-[:HAS_FEATURE]->(f)

// Get all categories with their subcategories
    // MATCH (c:Category)-[:HAS_SUBCATEGORY]->(s:SubCategory)
    // RETURN c.name AS Category, s.name AS SubCategory;

// Get features by category
    // MATCH (c:Category {name: "wpo_feature_agg_only"})-[:HAS_FEATURE]->(f:Feature)
    // RETURN c.name AS Category, f.name AS FeatureName, f.status;

// Get the complete hierarchy
    // MATCH path = (c:Category)-[:HAS_SUBCATEGORY]->(s:SubCategory)-[:HAS_FEATURE]->(f:Feature)
    // RETURN c.name AS Category, s.name AS SubCategory, f.name AS Feature;
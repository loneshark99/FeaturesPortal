from flask import Flask, render_template, request, redirect, url_for, flash
from neo4j import GraphDatabase

app = Flask(__name__, 
            template_folder='task_manager/templates',
            static_folder='task_manager/static')
app.secret_key = "your_secret_key"

# Neo4j connection setup
class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_session(self):
        return self.driver.session()

# Initialize Neo4j connection (modify credentials as needed)
neo4j_conn = Neo4jConnection("bolt://localhost:7687", "neo4j", "test1111")

# Routes
@app.route('/')
def index():
    with neo4j_conn.get_session() as session:
        # Get all features with their categories and subcategories
        result = session.run("""
            MATCH (f:Feature)
            OPTIONAL MATCH (c:Category)-[:HAS_FEATURE]->(f)
            OPTIONAL MATCH (s:SubCategory)-[:HAS_FEATURE]->(f)
            RETURN f, c.name as category, s.name as subcategory
            ORDER BY f.featureId
            LIMIT 25                
        """)
        features = []
        for record in result:
            feature = dict(record['f'])
            features.append({
                'id': feature.get('featureId'),
                'name': feature.get('name'),
                'project': feature.get('project'),
                'category': record['category'],
                'subcategory': record['subcategory'],
                'dataType': feature.get('dataType'),
                'description': feature.get('description'),
                'status': feature.get('status'),
                'source': feature.get('source'),
                'owner': feature.get('owner')
            })
        
        # Get all categories and subcategories for the dropdowns
        categories_result = session.run("MATCH (c:Category) RETURN c.name as name ORDER BY c.name")
        categories = [record['name'] for record in categories_result]
        
        subcategories_result = session.run("MATCH (s:SubCategory) RETURN s.name as name ORDER BY s.name")
        subcategories = [record['name'] for record in subcategories_result]
        
        return render_template('index.html', features=features, categories=categories, subcategories=subcategories)

@app.route('/add', methods=['POST'])
def add_feature():
    # Get form data
    feature_name = request.form['feature_name']
    project = request.form['project']
    category = request.form['category']
    subcategory = request.form['subcategory']
    data_type = request.form['data_type']
    description = request.form['description']
    status = request.form['status']
    source = request.form['source']
    owner = request.form['owner']
    
    if not feature_name:
        flash('Feature name is required!')
        return redirect(url_for('index'))
    
    with neo4j_conn.get_session() as session:
        # Get the next featureId
        max_id_result = session.run("MATCH (f:Feature) RETURN COALESCE(MAX(f.featureId), 0) as max_id")
        next_id = max_id_result.single()['max_id'] + 1
        
        # Create the feature node
        session.run("""
            CREATE (f:Feature {
                featureId: $id,
                name: $name,
                project: $project,
                dataType: $data_type,
                description: $description,
                status: $status,
                source: $source,
                owner: $owner
            })
        """, id=next_id, name=feature_name, project=project, data_type=data_type,
             description=description, status=status, source=source, owner=owner)
        
        # Connect to category if provided
        if category:
            session.run("""
                MATCH (f:Feature {featureId: $id})
                MERGE (c:Category {name: $category})
                MERGE (c)-[:HAS_FEATURE]->(f)
            """, id=next_id, category=category)
        
        # Connect to subcategory if provided
        if subcategory:
            session.run("""
                MATCH (f:Feature {featureId: $id})
                MERGE (s:SubCategory {name: $subcategory})
                MERGE (s)-[:HAS_FEATURE]->(f)
                
                // Also ensure subcategory is connected to category if both are provided
                WITH s
                MATCH (c:Category {name: $category})
                MERGE (c)-[:HAS_SUBCATEGORY]->(s)
            """, id=next_id, subcategory=subcategory, category=category)
    
    flash('Feature added successfully!')
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update_feature(id):
    # Get form data
    feature_name = request.form['feature_name']
    project = request.form['project']
    category = request.form['category']
    subcategory = request.form['subcategory']
    data_type = request.form['data_type']
    description = request.form['description']
    status = request.form['status']
    source = request.form['source']
    owner = request.form['owner']
    
    if not feature_name:
        flash('Feature name is required!')
        return redirect(url_for('index'))
    
    with neo4j_conn.get_session() as session:
        # Update the feature node
        session.run("""
            MATCH (f:Feature {featureId: $id})
            SET f.name = $name,
                f.project = $project,
                f.dataType = $data_type,
                f.description = $description,
                f.status = $status,
                f.source = $source,
                f.owner = $owner
        """, id=id, name=feature_name, project=project, data_type=data_type,
             description=description, status=status, source=source, owner=owner)
        
        # Remove existing category relationships
        session.run("""
            MATCH (f:Feature {featureId: $id})
            MATCH (c:Category)-[r:HAS_FEATURE]->(f)
            DELETE r
        """, id=id)
        
        # Remove existing subcategory relationships
        session.run("""
            MATCH (f:Feature {featureId: $id})
            MATCH (s:SubCategory)-[r:HAS_FEATURE]->(f)
            DELETE r
        """, id=id)
        
        # Connect to category if provided
        if category:
            session.run("""
                MATCH (f:Feature {featureId: $id})
                MERGE (c:Category {name: $category})
                MERGE (c)-[:HAS_FEATURE]->(f)
            """, id=id, category=category)
        
        # Connect to subcategory if provided
        if subcategory:
            session.run("""
                MATCH (f:Feature {featureId: $id})
                MERGE (s:SubCategory {name: $subcategory})
                MERGE (s)-[:HAS_FEATURE]->(f)
                
                // Also ensure subcategory is connected to category if both are provided
                WITH s
                MATCH (c:Category {name: $category})
                MERGE (c)-[:HAS_SUBCATEGORY]->(s)
            """, id=id, subcategory=subcategory, category=category)
    
    flash('Feature updated successfully!')
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_feature(id):
    with neo4j_conn.get_session() as session:
        # Delete the feature
        session.run("""
            MATCH (f:Feature {featureId: $id})
            DETACH DELETE f
        """, id=id)
    
    flash('Feature deleted successfully!')
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search_by_category():
    category = request.args.get('category', '')
    
    if not category:
        flash('Please select a category to search!')
        return redirect(url_for('index'))
    
    with neo4j_conn.get_session() as session:
        # Get features by category
        result = session.run("""
            MATCH (c:Category {name: $category})-[:HAS_FEATURE]->(f:Feature)
            OPTIONAL MATCH (s:SubCategory)-[:HAS_FEATURE]->(f)
            RETURN f, c.name as category, s.name as subcategory
            ORDER BY f.featureId
        """, category=category)
        
        features = []
        for record in result:
            feature = dict(record['f'])
            features.append({
                'id': feature.get('featureId'),
                'name': feature.get('name'),
                'project': feature.get('project'),
                'category': record['category'],
                'subcategory': record['subcategory'],
                'dataType': feature.get('dataType'),
                'description': feature.get('description'),
                'status': feature.get('status'),
                'source': feature.get('source'),
                'owner': feature.get('owner')
            })
        
        # Get all categories and subcategories for the dropdowns
        categories_result = session.run("MATCH (c:Category) RETURN c.name as name ORDER BY c.name")
        categories = [record['name'] for record in categories_result]
        
        subcategories_result = session.run("MATCH (s:SubCategory) RETURN s.name as name ORDER BY s.name")
        subcategories = [record['name'] for record in subcategories_result]
        
        return render_template('search_results.html', 
                              features=features, 
                              categories=categories, 
                              subcategories=subcategories,
                              search_category=category)

if __name__ == '__main__':
    app.run(debug=True)
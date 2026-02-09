from flask import Flask,render_template,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime,timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import func
import pandas as pd

current_dir=os.path.abspath(os.path.dirname(__file__))
URI="sqlite:///"+os.path.join(current_dir,"database.db")
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = URI
db=SQLAlchemy()
db.init_app(app)
app.app_context().push()
app.secret_key = 'your_secret_key'

#models
class ToDo(db.Model):
    __tablename__ = 'ToDo'
    
    ListID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(255), nullable=False)
    Description = db.Column(db.Text, nullable=False)
    StartDate = db.Column(db.Date, nullable=False)
    FinishDate = db.Column(db.Date)
    DueDate = db.Column(db.Date)
    Category = db.Column(db.String(255), nullable=False)
    Subject = db.Column(db.String(255), nullable=False)
    Topic = db.Column(db.String(255))
    Status = db.Column(db.String(20), nullable=False)
    Result = db.Column(db.Integer)
    Feedback = db.Column(db.Text)
    Remarks = db.Column(db.Text)
    Type = db.Column(db.Text)

    __table_args__=(
        db.CheckConstraint("Status IN ('Pending', 'Submitted','Due Date Passed','Cancelled')", name='check_status'),
        db.CheckConstraint("Type IN ('Assignment', 'LongAssignment','Project','Event','Test')", name='check_type'),
    )


# Controllers
today=datetime.today().date()

#Functions
def up_assign(todos,interval): # 7 -> No. of x_values ; interval -> Interval
    counts = {}
    for i in range(7):
        start_of_week = today + timedelta(days=i * interval)
        end_of_week = today + timedelta(days=(i + 1) * interval - 1)
        try:
            count = sum(start_of_week <= todo.DueDate <= end_of_week for todo in todos)
            # print("WORKING",start_of_week,end_of_week,count)
        except:
            count = 0
            # print("NOT WORKING",todos)
        finally:
            counts[f'{start_of_week.strftime("%d-%m")}  to  {end_of_week.strftime("%d-%m")}'] = count
    return counts

def past_assign(todos,interval):
    counts = {}
    for i in range(7):
        start_of_week = today - timedelta(days=(i + 1) * interval - 1)
        end_of_week = today - timedelta(days=i * interval)
        try:
            count = sum(start_of_week <= todo.FinishDate <= end_of_week for todo in todos)
        except:
            count = 0
        finally:
            counts[f'{start_of_week.strftime("%d-%m")} to {end_of_week.strftime("%d-%m")}'] = count
        
    return dict(reversed(counts.items()))

def path(link):
    image_path = 'static/images'
    abs_path = os.path.abspath(image_path)
    full_path = os.path.join(abs_path, link)
    return full_path

def plot_bar(dict,title):
    labels=list(dict.keys())
    values=list(dict.values())

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color='darkblue')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Week Range')
    plt.ylabel('Number of Assignments')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path(f'Dashboard/{title}.jpg'))
    plt.close()

types = ('Assignment', 'LongAssignment','Project','Event','Test')


@app.route('/update_type')
def update_type():
    new_type = request.args.get('new_type', 'default')
    session['type'] = new_type
    return redirect('/Dashboard')

@app.route(f'/Dashboard',methods=['GET'])
def Dashboard():

    if 'type' not in session: # init
        session['type'] = 'Assignment'

    # Update the session with the new 'type' if passed in the query string
    new_type = request.args.get('new_type')
    if new_type:
        session['type'] = new_type

    type = session.get('type')

    match type: # match case
        case 'Assignment':
            interval = 2
        case 'LongAssignment':
            interval = 7
        case 'Project':
            interval = 10
        case 'Event' | 'Test':
            interval = 1
        case _: # error handling
            ValueError("Incorrect type")

    todos = (db.session.query(ToDo)
             .filter(ToDo.Type == type)
             .all())
    
    print([todo.DueDate for todo in todos])
    
    todays = list(filter(lambda todo: todo.Status == 'Pending'
                        and todo.DueDate == today,todos))
    
    tomos = list(filter(lambda todo: todo.Status == 'Pending' 
                        and todo.DueDate == today + timedelta(days=1),todos))
    
    due = list(filter(lambda todo: todo.Status=='Pending'
                        and todo.DueDate < today,todos))

    up = list(filter(lambda todo: todo.DueDate <= today + timedelta( days = interval * 7)
                     and todo.Status == 'Pending',todos))
    
    prev = list(filter(lambda todo: todo.DueDate <= today
                       and todo.Status == 'Pending',todos))
    
    for i in due:
        i.Status='Due Date Passed'
        i.Result=0
        i.Feedback='Auto Failure'
        db.session.commit()
    
    plot_bar(up_assign(up,interval),f'Upcoming {type}s')
    plot_bar(past_assign(prev,interval),f'Past {type}s')

    return render_template(f'Dashboard.html',
                           todays=todays,
                           tomos=tomos,
                           due=due,
                           type=type,
                           types=types)

@app.route('/Pending',methods=["GET"])
def Pending():
    type = session.get('type')
    pending=(db.session.query(ToDo)
             .filter(ToDo.Status=='Pending',ToDo.Type == type)
             .order_by(ToDo.DueDate)
             .all())
    return render_template('Pending.html',pending=pending,type=type)

@app.route('/Completed',methods=['GET'])
def Completed():
    type = session.get('type')
    completed=(db.session.query(ToDo)
               .filter(ToDo.Status=='Submitted',ToDo.Type==type )
               .order_by(ToDo.FinishDate.desc())
               .all())
    return render_template('Completed.html',completed=completed,type=type)

@app.route('/Failed',methods=['GET'])
def Failed():
    type = session.get('type')
    failed=(db.session.query(ToDo).filter(ToDo.Status=='Due Date Passed',ToDo.Type == type)
            .order_by(ToDo.DueDate.desc())
            .all())
    return render_template('Failed.html',failed=failed,type=type)

@app.route('/Cancelled',methods=['GET'])
def Cancelled():
    type = session.get('type')
    cancelled=(db.session.query(ToDo).filter(ToDo.Status=='Cancelled',ToDo.Type == type)
               .order_by(ToDo.DueDate.desc())
               .all())
    return render_template('Cancelled.html',cancelled=cancelled,type=type)

@app.route('/All',methods=["GET"])
def All():
    type = session.get('type')
    all=(db.session.query(ToDo)
         .filter(ToDo.Type == type)
         .order_by(ToDo.DueDate.desc())
         .all())
    
    return render_template('All.html',all=all,type=type)

@app.route('/Details/<int:ListID>',methods=['GET'])
def Details(ListID):
    type = session.get('type')
    assign=db.session.query(ToDo).filter(ToDo.ListID==ListID).one()
    return render_template('Details.html',assign=assign,type=type)

@app.route('/Create',methods=['GET','POST'])
def Create():
    type = session.get('type')
    if request.method=='POST':
        name=request.form['name']
        description=request.form['description']
        duedate = datetime.strptime(request.form['duedate'], '%Y-%m-%d').date()
        category=request.form['category']
        subject=request.form['subject']
        topic=request.form['topic']
        type=request.form['type']
        remarks=request.form['remarks']
        new_assign=ToDo(
            Name=name,
            Description=description,
            StartDate=today,
            DueDate=duedate,
            Category=category,
            Subject=subject,
            Topic=topic,
            Remarks=remarks,
            Status='Pending',
            Type=type
        )
        db.session.add(new_assign)
        db.session.commit()
        return redirect(f'/Dashboard')
    return render_template('Create.html',today=today,type=type)

@app.route('/Submit/<int:ListID>',methods=['GET','POST'])
def Submit(ListID):
    assign=db.session.query(ToDo).filter(ToDo.ListID==ListID).one()
    if request.method=='POST':
        assign.FinishDate=today
        assign.Status='Submitted'
        assign.Result=request.form['result']
        assign.Feedback=request.form['feedback']
        db.session.commit()
        return redirect(f'/Details/{ListID}')
    return render_template('Submit.html',assign=assign)

@app.route('/Edit/<int:ListID>',methods=["GET",'POST'])
def Edit(ListID):
    assign=db.session.query(ToDo).filter(ToDo.ListID==ListID).one()
    if request.method=='POST':
        assign.Description=request.form['description']
        assign.DueDate=datetime.strptime(request.form['duedate'], '%Y-%m-%d').date()
        assign.Category=request.form['category']
        assign.Subject=request.form['subject']
        assign.Topic=request.form['topic']
        assign.Remarks=request.form['remarks']
        assign.Status='Pending'
        db.session.commit()
        return redirect(f'/Details/{ListID}')
    return render_template('Edit.html',assign=assign,today=today)

@app.route('/Cancel/<int:ListID>',methods=["GET",'POST'])
def Cancel(ListID):
    assign=db.session.query(ToDo).filter(ToDo.ListID==ListID).one()
    if request.method=='POST':
        assign.Feedback=request.form['feedback']
        assign.Status='Cancelled'
        db.session.commit()
        return redirect(f'/Details/{ListID}')
    return render_template('Cancel.html',assign=assign)

@app.route('/Feedback/<int:ListID>',methods=["GET",'POST'])
def Feedback(ListID):
    assign=db.session.query(ToDo).filter(ToDo.ListID==ListID).one()
    if request.method=='POST':
        assign.Result=request.form['result']
        assign.Feedback=request.form['feedback']
        db.session.commit()
        return redirect(f'/Details/{ListID}')
    return render_template('Feedback.html',assign=assign)

@app.route('/Category',methods=['GET'])
def Category():
    type = session.get('type')
    categories = (db.session
                  .query(ToDo.Category,func.count(ToDo.Category).label('count'))
                  .filter(ToDo.Type == type).group_by(ToDo.Category)
                  .order_by(func.count(ToDo.Category).desc())
                  .all())
    return render_template('By_Category.html',categories=categories,type=type)

@app.route('/Cat_assign/<string:Category>',methods=['GET'])
def Cat_Assign(Category):
    assign=db.session.query(ToDo).filter(ToDo.Category==Category).order_by(ToDo.DueDate.desc()).all()
    return render_template('Category.html',Category=Category,assign=assign)



if __name__=='__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )



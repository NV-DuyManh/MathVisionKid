from pathlib import Path
import zipfile,subprocess,os,re,sys,json
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'report/codex-antigravity-review-20261029'; OUT.mkdir(exist_ok=True); env=os.environ.copy()
for file in [ROOT/'.env',ROOT/'backend/business-api/.env']:
    if file.exists():
        for line in file.read_text(encoding='utf-8-sig').splitlines():
            m=re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$',line)
            if m:env[m[1]]=m[2].strip('\"\'')
jar=ROOT/'backend/business-api/build/libs/business-api.jar'
with zipfile.ZipFile(jar) as z:
    name=next(n for n in z.namelist() if re.match(r'BOOT-INF/lib/postgresql-[^/]+\.jar$',n)); (OUT/'postgresql.jar').write_bytes(z.read(name))
java=OUT/'ReviewSql.java'
java.write_text('''import java.sql.*;
public class ReviewSql {
 public static void main(String[] args) throws Exception {
  String query=new String(System.in.readAllBytes(),java.nio.charset.StandardCharsets.UTF_8);
  try(var c=DriverManager.getConnection(System.getenv("DB_URL"),System.getenv("DB_USERNAME"),System.getenv("DB_PASSWORD"));var st=c.createStatement()) {
   st.setQueryTimeout(20); boolean result=st.execute(query);
   do { if(result) {try(var rs=st.getResultSet()){while(rs.next())System.out.println(rs.getString(1));}}else if(st.getUpdateCount()==-1)break;
   result=st.getMoreResults(); }while(true);
  }
 }
}''',encoding='utf-8')
subprocess.run(['javac',str(java)],check=True)
def sql(query,db=None):
    e=env.copy()
    if db:e['DB_URL']='jdbc:postgresql://127.0.0.1:5432/'+db
    p=subprocess.run(['java','-Dfile.encoding=UTF-8','-cp',str(OUT)+';'+str(OUT/'postgresql.jar'),'ReviewSql'],input=query.encode('utf-8'),capture_output=True,env=e,timeout=30)
    if p.returncode:raise RuntimeError(p.stderr.decode('utf-8','replace'))
    return p.stdout.decode('utf-8').strip()
if __name__=='__main__':
    print('PostgreSQL',sql('SELECT version()'),flush=True)
    print('Main migrations',sql("SELECT coalesce(json_agg(row_to_json(t)), '[]') FROM (SELECT version,description,success,installed_on FROM flyway_schema_history ORDER BY installed_rank DESC LIMIT 5)t"),flush=True)
    print('Existing duplicates across source types',sql("SELECT count(*) FROM (SELECT student_id,source_fingerprint FROM student_quizzes GROUP BY student_id,source_fingerprint HAVING count(*)>1)t"),flush=True)
    print('DB checks',sql("SELECT json_agg(pg_get_constraintdef(oid)) FROM pg_constraint WHERE conrelid='student_quizzes'::regclass AND contype='c'"),flush=True)

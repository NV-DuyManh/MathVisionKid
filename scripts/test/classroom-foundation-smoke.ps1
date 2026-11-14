$ErrorActionPreference='Stop'
$base='http://127.0.0.1:18084/api/v1'
function Call($method,$path,$auth,$body) {
 $params=@{Method=$method;Uri="$base$path";SkipHttpErrorCheck=$true}
 if($auth){$params.Headers=@{Authorization="Bearer $auth"}}
 if($null -ne $body){$params.ContentType='application/json';$params.Body=ConvertTo-Json -Compress -InputObject $body}
 $r=Invoke-WebRequest @params
 $data=if($r.Content){ConvertFrom-Json $r.Content}else{$null}
 return @{status=[int]$r.StatusCode;data=$data}
}
function Assert($condition,$message){if(-not $condition){throw $message};Write-Output "PASS $message"}
function Login($email,$password){(Call POST '/auth/login' $null @{email=$email;password=$password}).data.accessToken}
$teacher=Login 'lan.teacher@mathvision.local' '123'

$admin=Login 'admin.demo@mathvision.local' '123'

function CreateStudent($name) {
 $email='foundation.student.'+[guid]::NewGuid().ToString('N')+'@mathvision.test'
 $pw=[guid]::NewGuid().ToString('N')
 $response=Call POST '/admin/users' $admin @{email=$email;displayName=$name;role='STUDENT';gradeLevel=3;initialPassword=$pw}
 if($response.status -ne 201){throw 'Could not provision synthetic Student'}
 return Login $email $pw
}
$student=CreateStudent 'Foundation QA Student One'
$secondStudent=CreateStudent 'Foundation QA Student Two'

$email='foundation.next.'+[guid]::NewGuid().ToString('N')+'@mathvision.test'
$pw=[guid]::NewGuid().ToString('N')
$createdTeacher=Call POST '/admin/users' $admin @{email=$email;displayName='Foundation QA Teacher';role='TEACHER';initialPassword=$pw}
Assert ($createdTeacher.status -eq 201) 'Admin provisions a synthetic successor'
$successor=Login $email $pw
$classBody=@{name='QA Classroom';gradeLevel=3;requestId=[guid]::NewGuid()}
$created=Call POST '/teacher/classes' $teacher $classBody
Assert ($created.status -eq 201 -and $created.data.joinMode -eq 'APPROVAL_REQUIRED') 'Teacher creates approval class'
$id=$created.data.classId
$route="/teacher/classes/$id"
Assert ((Call POST '/teacher/classes' $teacher $classBody).data.classId -eq $id) 'Create replay converges'
Assert ((Call PATCH $route $successor @{gradeLevel=4}).status -eq 403) 'Other Teacher cannot edit'
Assert ((Call POST '/teacher/classes' $student $classBody).status -eq 403) 'Student cannot create classroom'
$invite=(Call POST "$route/invitation" $teacher $null).data
$first=Call POST '/student/classes/invitation-preview' $student @{credential=$invite.code}
$join=@{credential=$invite.code;classId=$id;generation=$first.data.generation}
Assert ((Call POST '/student/classes/join' $student $join).data.status -eq 'PENDING') 'Approval path creates Pending'
Assert ((Call POST '/student/classes/join' $student $join).data.status -eq 'PENDING') 'Pending replay converges'
$req=(Call GET "$route/join-requests" $teacher $null).data[0]
Assert ((Call PATCH $route $teacher @{joinMode='AUTO_JOIN'}).status -eq 204) 'Teacher changes mode'
Assert ((Call POST '/student/classes/join' $student $join).data.status -eq 'PENDING') 'Old Pending survives mode change'
$decision="$route/join-requests/$($req.studentId)"
Assert ((Call PUT $decision $teacher @{requestId=$req.requestId;approve=$false}).status -eq 204) 'Teacher declines pending'
Assert ((Call POST '/student/classes/join' $student $join).data.status -eq 'PENDING') 'Declined pupil cannot bypass Auto Join'
$new=(Call POST "$route/invitation" $teacher $null).data
Assert ((Call POST '/student/classes/join' $student $join).status -eq 404) 'Stale confirmation rejected after rotation'
Assert ((Call POST '/student/classes/invitation-preview' $student @{credential=$invite.token}).status -eq 404) 'Old link token rejected'
$join2=@{credential=$new.token;classId=$id;generation=$new.generation}
Assert ((Call POST '/student/classes/join' $secondStudent $join2).data.status -eq 'JOINED') 'Auto Join admits eligible pupil'
Assert ((Call POST '/student/classes/join' $secondStudent $join2).data.status -eq 'JOINED') 'Membership replay converges'
$members=(Call GET $route $teacher $null).data.students
Assert (@($members).Count -eq 1) 'Roster has no duplicate membership'
Assert ((Call DELETE "$route/students/$($members[0].userId)" $teacher $null).status -eq 204) 'Teacher removes pupil'
Assert ((Call POST '/student/classes/join' $secondStudent $join2).data.status -eq 'PENDING') 'Removed pupil cannot bypass Auto Join'
Assert ((Call PUT "/admin/classes/$id/teacher" $admin @{teacherId=$createdTeacher.data.userId}).status -eq 200) 'Admin hands over classroom'
Assert ((Call GET "$route/invitation" $teacher $null).status -eq 403) 'Old Teacher loses invitation read'
Assert ((Call PATCH $route $teacher @{gradeLevel=4}).status -eq 403) 'Old Teacher loses mutation'
Assert ((Call GET "$route/invitation" $successor $null).data.generation -eq $new.generation) 'Successor inherits valid invitation'
Assert (@((Call GET "$route/join-requests" $successor $null).data).Count -eq 2) 'Successor inherits both Pending requests'
Assert ((Call DELETE "$route/invitation" $successor $null).status -eq 204) 'Successor disables invitation'
Assert ((Call POST '/student/classes/invitation-preview' $secondStudent @{credential=$new.code}).status -eq 404) 'Disabled code rejected'

$pending=(Call GET "$route/join-requests" $successor $null).data[0]
$client=[System.Net.Http.HttpClient]::new()
try {
 $client.DefaultRequestHeaders.Authorization=[System.Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$successor)
 $json=ConvertTo-Json -Compress @{requestId=$pending.requestId;approve=$true}
 $url="$base$route/join-requests/$($pending.studentId)"
 $first=$client.PutAsync($url,[System.Net.Http.StringContent]::new($json,[Text.Encoding]::UTF8,'application/json'))
 $second=$client.PutAsync($url,[System.Net.Http.StringContent]::new($json,[Text.Encoding]::UTF8,'application/json'))
 Assert ($first.GetAwaiter().GetResult().StatusCode -eq 204 -and $second.GetAwaiter().GetResult().StatusCode -eq 204) 'Concurrent duplicate approvals converge'
 $roster=(Call GET $route $successor $null).data.students
 Assert (@($roster).Count -eq 1 -and $roster[0].userId -eq $pending.studentId) 'Concurrent approval creates one membership'
} finally {$client.Dispose()}

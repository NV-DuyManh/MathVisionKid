import { Ionicons } from '@expo/vector-icons';
import { Image } from 'react-native';
import StudentLoginScreen from '../components/auth/StudentLoginForm';
import { studentAuthStyles } from '../components/auth/studentAuthStyles.web';

const learningHighlights = [
  { icon: 'checkmark', text: 'Bài học dễ hiểu' },
  { icon: 'sparkles-outline', text: 'AI đồng hành' },
  { icon: 'ribbon-outline', text: 'Tích sao mỗi ngày' },
] as const;

export default function WebLoginEntry() {
  return (
    <div className="student-auth">
      <style>{studentAuthStyles}</style>
      <section className="student-auth-hero" aria-label="MathVisionKid">
        <div className="student-auth-brand">
          <span aria-hidden="true"><Ionicons name="sparkles" size={17} /></span>
          Math<span className="student-auth-brand-accent">Vision</span>Kid
        </div>
        <div className="student-auth-intro">
          <p className="student-auth-slogan">Mỗi bài toán,<br /><span>một khám phá.</span></p>
          <p className="student-auth-description">Cùng MathVisionKid học Toán qua luyện tập, trò chơi và khám phá AI.</p>
          <ul className="student-auth-highlights">
            {learningHighlights.map(({ icon, text }) => (
              <li key={icon}><Ionicons name={icon} size={17} accessible={false} />{text}</li>
            ))}
          </ul>
        </div>
        <div className="student-auth-art" aria-hidden="true">
          <Image
            source={require('../../assets/illustrations/web/robot-mascot.webp')}
            resizeMode="contain"
            style={{ width: '100%', aspectRatio: 1 }}
            accessible={false}
          />
          <span>8 + 5 = 13</span>
          <span>△ □ ○</span>
        </div>
      </section>
      <main className="student-auth-main">
        <StudentLoginScreen webLayout />
      </main>
    </div>
  );
}

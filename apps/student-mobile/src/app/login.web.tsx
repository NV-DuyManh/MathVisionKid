import { Ionicons } from '@expo/vector-icons';
import { Image } from 'react-native';
import StudentLoginScreen from '../components/auth/StudentLoginForm';
import { studentAuthStyles } from '../components/auth/studentAuthStyles.web';

export default function WebLoginEntry() {
  return (
    <div className="student-auth">
      <style>{studentAuthStyles}</style>
      <div className="student-auth-layout">
        <section className="student-auth-hero" aria-label="Cùng em khám phá Toán học">
          <div className="student-auth-brand">
            <Ionicons name="planet" size={25} color="#FFE07C" aria-hidden />
            <span>MathVisionKid</span>
          </div>
          <div className="student-auth-intro">
            <p className="student-auth-slogan">Mỗi bài toán,<br /><span>một khám phá.</span></p>
            <p className="student-auth-description">Cùng MathVisionKid học Toán qua luyện tập, trò chơi và khám phá AI.</p>
          </div>
          <div className="student-auth-art" aria-hidden="true">
            <Image
              source={require('../../assets/illustrations/web/robot-mascot.webp')}
              resizeMode="contain"
              style={{ width: '100%', aspectRatio: 1 }}
              accessible={false}
            />
          </div>
          <span className="student-auth-math" aria-hidden><b>8 + 5 = 13</b><Ionicons name="shapes-outline" size={30} color="#D7F6FF" /></span>
        </section>
        <main className="student-auth-main">
          <StudentLoginScreen webLayout />
        </main>
      </div>
    </div>
  );
}

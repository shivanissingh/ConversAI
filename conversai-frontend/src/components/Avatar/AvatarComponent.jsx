import { Player } from '@lottiefiles/react-lottie-player'
import { useRef } from 'react'
import styles from './AvatarComponent.module.css'

export default function AvatarComponent({ isSpeaking, intensity = 'medium' }) {
  const playerRef = useRef(null)

  return (
    <div className={styles.container}>
      <div className={styles.avatarWrapper}>
        <Player
          ref={playerRef}
          src={isSpeaking ? '/lottie/speaking.json' : '/lottie/idle.json'}
          loop
          autoplay
          style={{ width: '100%', height: '100%' }}
        />
      </div>
      <div className={styles.soundwave}>
        {[0, 1, 2, 3, 4].map(i => (
          <div
            key={i}
            className={`${styles.bar} ${isSpeaking ? styles.barActive : ''}`}
            style={{
              animationDelay: `${[0, 0.1, 0.2, 0.1, 0][i]}s`,
              animationDuration: intensity === 'high' ? '0.3s' : intensity === 'low' ? '0.8s' : '0.5s'
            }}
          />
        ))}
      </div>
      <div className={styles.status}>
        {isSpeaking
          ? <span className={styles.speaking}>● Speaking</span>
          : <span className={styles.idle}>○ Idle</span>
        }
      </div>
    </div>
  )
}

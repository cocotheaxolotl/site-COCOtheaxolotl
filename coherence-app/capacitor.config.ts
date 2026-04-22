import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.loopinky.coco.coherence',
  appName: 'Coco Cohérence',
  webDir: 'www',
  server: {
    androidScheme: 'https'
  },
  android: {
    backgroundColor: '#1a1a2e'
  }
};

export default config;

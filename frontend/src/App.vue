<script>
import { useUserStore } from '@/store/user';

export default {
  onLaunch() {
    const userStore = useUserStore();
    userStore.initFriendIdentity().catch((error) => {
      console.warn('Friend identity initialization failed', error);
    });
  }
};
</script>

<style lang="scss">
@import '@/uni.scss';

page {
  background-color: $uni-bg-color-grey;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: $uni-text-color;
  font-size: $uni-font-size-base;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

view, scroll-view, swiper, swiper-item, cover-view, cover-image, icon, text, rich-text, progress, button, checkbox, form, input, label, radio, slider, switch, textarea, navigator, audio, camera, image, video {
  box-sizing: border-box;
}

.title-large {
  font-size: $uni-font-size-title;
  font-weight: 700;
  color: $uni-text-color;
  letter-spacing: -0.5px;
  margin-bottom: $uni-spacing-col-base;
}

.card {
  background-color: $uni-bg-color;
  border-radius: $uni-border-radius-base;
  padding: $uni-spacing-row-base;
  box-shadow: $uni-shadow-sm;
  margin-bottom: $uni-spacing-col-base;
}

.btn-primary {
  background-color: $uni-color-primary;
  color: #FFFFFF;
  border-radius: $uni-border-radius-lg;
  font-weight: 600;
  border: none;

  &:active {
    opacity: 0.8;
  }
}
</style>

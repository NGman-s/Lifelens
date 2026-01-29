<template>
  <view class="page-container">
    <view class="content-wrapper">
      <view class="header">
        <text class="title-large">我的档案</text>
      </view>

      <!-- Personal Info Section -->
      <view class="section-title">基本信息</view>
      <view class="list-group">
        <view class="list-item">
          <text class="item-label">性别</text>
          <picker
            @change="handleGenderChange"
            :value="genders.findIndex(g => g.value === profile.gender)"
            :range="genders"
            range-key="label"
            class="picker-container"
          >
            <view class="picker-content">
              <text class="picker-value">{{ currentGenderLabel }}</text>
              <text class="chevron">›</text>
            </view>
          </picker>
        </view>
        <view class="list-divider"></view>

        <view class="list-item">
          <text class="item-label">年龄</text>
          <input
            class="item-input"
            type="number"
            v-model="profile.age"
            @blur="saveProfile"
            placeholder="请输入年龄"
          />
        </view>
        <view class="list-divider"></view>

        <view class="list-item">
          <text class="item-label">身高 (cm)</text>
          <input
            class="item-input"
            type="number"
            v-model="profile.height"
            @blur="saveProfile"
            placeholder="cm"
          />
        </view>
        <view class="list-divider"></view>

        <view class="list-item">
          <text class="item-label">体重 (kg)</text>
          <input
            class="item-input"
            type="number"
            v-model="profile.weight"
            @blur="saveProfile"
            placeholder="kg"
          />
        </view>
        <view class="list-divider"></view>

        <view class="list-item">
          <text class="item-label">活动量</text>
          <picker
            @change="handleActivityChange"
            :value="activityLevels.findIndex(a => a.value === profile.activity_level)"
            :range="activityLevels"
            range-key="label"
            class="picker-container"
          >
            <view class="picker-content">
              <text class="picker-value">{{ currentActivityLabel }}</text>
              <text class="chevron">›</text>
            </view>
          </picker>
        </view>
        <view class="list-divider"></view>

        <view class="list-item">
          <text class="item-label">饮食目标</text>
          <picker
            @change="handleGoalChange"
            :value="goals.findIndex(g => g.value === profile.goal)"
            :range="goals"
            range-key="label"
            class="picker-container"
          >
            <view class="picker-content">
              <text class="picker-value">{{ currentGoalLabel }}</text>
              <text class="chevron">›</text>
            </view>
          </picker>
        </view>
      </view>

      <!-- Health Conditions Section -->
      <view class="section-title">健康偏好</view>
      <view class="list-group">
        <view class="list-item condition-row">
          <text class="item-label">饮食禁忌与状况</text>
        </view>
        <view class="list-divider"></view>
        <view class="conditions-container">
          <!-- Preset Conditions -->
          <view
            v-for="condition in healthConditions"
            :key="condition.value"
            class="chip"
            :class="{ active: profile.health_conditions.includes(condition.value) }"
            @tap="toggleCondition(condition.value)"
          >
            {{ condition.label }}
          </view>

          <!-- Custom Conditions -->
          <view
            v-for="condition in customConditionsList"
            :key="condition"
            class="chip active"
            @tap="removeCustomCondition(condition)"
          >
            {{ condition }} <text class="chip-remove">×</text>
          </view>
        </view>

        <view class="list-divider"></view>

        <!-- Add Custom Condition -->
        <view class="list-item custom-input-row">
           <input
            class="custom-input"
            type="text"
            v-model="customCondition"
            placeholder="添加其他 (如: 海鲜过敏)"
            confirm-type="done"
            @confirm="addCustomCondition"
          />
          <view class="add-btn" @tap="addCustomCondition" :class="{ disabled: !customCondition.trim() }">
            添加
          </view>
        </view>
      </view>

      <view class="info-footer">
        <text class="info-text">LifeLens AI 将根据您的档案提供个性化建议。</text>
      </view>
    </view>

    <BottomNav current="profile" />
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useUserStore } from '@/store/user';
import { storeToRefs } from 'pinia';
import BottomNav from '@/components/BottomNav.vue';

const userStore = useUserStore();
const { profile } = storeToRefs(userStore);

const customCondition = ref('');

const goals = [
  { label: '增肌', value: 'muscle_gain' },
  { label: '减脂', value: 'weight_loss' },
  { label: '健康饮食', value: 'healthy_eat' },
  { label: '糖尿病管理', value: 'diabetes' }
];

const genders = [
  { label: '男', value: 'male' },
  { label: '女', value: 'female' },
  { label: '其他', value: 'other' }
];

const activityLevels = [
  { label: '久坐不动', value: 'sedentary' },
  { label: '轻度活动', value: 'lightly_active' },
  { label: '中度活动', value: 'moderately_active' },
  { label: '非常活跃', value: 'very_active' },
  { label: '极度活跃', value: 'extra_active' }
];

const healthConditions = [
  { label: '高血压', value: 'Hypertension' },
  { label: '糖尿病', value: 'Diabetes' },
  { label: '高胆固醇', value: 'High Cholesterol' },
  { label: '无麸质', value: 'Gluten Free' },
  { label: '坚果过敏', value: 'Nut Allergy' },
  { label: '乳糖不耐受', value: 'Lactose Intolerant' }
];

const currentGoalLabel = computed(() => {
  const goal = goals.find(g => g.value === profile.value.goal);
  return goal ? goal.label : '选择目标';
});

const currentGenderLabel = computed(() => {
  const g = genders.find(i => i.value === profile.value.gender);
  return g ? g.label : '请选择';
});

const currentActivityLabel = computed(() => {
  const a = activityLevels.find(i => i.value === profile.value.activity_level);
  return a ? a.label : '请选择';
});

const handleGoalChange = (e) => {
  const index = e.detail.value;
  profile.value.goal = goals[index].value;
  saveProfile();
};

const handleGenderChange = (e) => {
  const index = e.detail.value;
  profile.value.gender = genders[index].value;
  saveProfile();
};

const handleActivityChange = (e) => {
  const index = e.detail.value;
  profile.value.activity_level = activityLevels[index].value;
  saveProfile();
};

const toggleCondition = (value) => {
  const index = profile.value.health_conditions.indexOf(value);
  if (index > -1) {
    profile.value.health_conditions.splice(index, 1);
  } else {
    profile.value.health_conditions.push(value);
  }
  saveProfile();
};

const addCustomCondition = () => {
  const val = customCondition.value.trim();
  if (val && !profile.value.health_conditions.includes(val)) {
    profile.value.health_conditions.push(val);
    saveProfile();
  }
  customCondition.value = '';
};

// Identify which conditions are custom (not in the preset list)
const customConditionsList = computed(() => {
  const presetValues = healthConditions.map(c => c.value);
  return profile.value.health_conditions.filter(c => !presetValues.includes(c));
});

const removeCustomCondition = (val) => {
  const index = profile.value.health_conditions.indexOf(val);
  if (index > -1) {
    profile.value.health_conditions.splice(index, 1);
    saveProfile();
  }
};

const saveProfile = () => {
  userStore.updateProfile(profile.value);
};
</script>

<style lang="scss" scoped>
.page-container {
  min-height: 100vh;
  padding-bottom: calc(50px + env(safe-area-inset-bottom));
}

.content-wrapper {
  padding: 20px;
}

.header {
  margin-bottom: 24px;
  padding-top: calc(env(safe-area-inset-top) + 20px);
}

.section-title {
  font-size: 13px;
  color: #86868b;
  margin-bottom: 8px;
  margin-left: 12px;
  text-transform: uppercase;
}

/* iOS Settings Group Style */
.list-group {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fff;
  min-height: 54px;
  box-sizing: border-box;
}

.list-divider {
  height: 1px;
  background: #f5f5f7;
  margin-left: 16px;
}

.item-label {
  font-size: 17px;
  color: #1d1d1f;
}

.item-input {
  text-align: right;
  font-size: 17px;
  color: #007aff;
  flex: 1;
  margin-left: 16px;
}

.picker-container {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.picker-content {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.picker-value {
  font-size: 17px;
  color: #86868b;
  margin-right: 8px;
}

.chevron {
  color: #c7c7cc;
  font-size: 20px;
  font-weight: 400;
  margin-top: -2px;
}

/* Chips for Conditions */
.conditions-container {
  padding: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  background: #fff;
}

.chip {
  padding: 8px 16px;
  background: #f5f5f7;
  border-radius: 100px;
  font-size: 14px;
  color: #1d1d1f;
  transition: all 0.2s ease;

  &.active {
    background: #007aff;
    color: #fff;
    box-shadow: 0 2px 8px rgba(0, 122, 255, 0.2);
  }
}

.chip-remove {
  margin-left: 4px;
  font-size: 16px;
  opacity: 0.6;
}

.custom-input-row {
  display: flex;
  align-items: center;
}

.custom-input {
  flex: 1;
  font-size: 16px;
  color: #1d1d1f;
  height: 40px;
}

.add-btn {
  margin-left: 12px;
  padding: 6px 12px;
  background-color: #007aff;
  color: white;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  transition: opacity 0.2s;

  &.disabled {
    opacity: 0.3;
    background-color: #8e8e93;
  }

  &:active {
    opacity: 0.7;
  }
}

.info-footer {
  margin-top: 8px;
  padding: 0 12px;
}

.info-text {
  font-size: 13px;
  color: #86868b;
  line-height: 1.4;
}
</style>

<template>
  <div class="login-container">
    <h2>用户登录</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>用户名：</label>
        <input
            type="text"
            v-model="form.username"
            placeholder="请输入用户名"
            required
        >
      </div>

      <div class="form-group">
        <label>密码：</label>
        <input
            type="password"
            v-model="form.password"
            placeholder="请输入密码"
            required
        >
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? '登录中...' : '立即登录' }}
      </button>

      <div v-if="errorMessage" class="error-msg">
        {{ errorMessage }}
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios';
import qs from 'qs';

export default {
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      loading: false,
      errorMessage: ''
    };
  },
  methods: {
    async handleLogin() {
      // 基础表单验证
      if (!this.form.username || !this.form.password) {
        this.errorMessage = '用户名和密码不能为空';
        return;
      }

      this.loading = true;
      this.errorMessage = '';

      try {
        const response = await axios.post(
            'http://localhost:7788/login',
            qs.stringify(this.form),
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
              withCredentials: true  // 允许携带cookie
            }
        );

        if (response.data.code === 0) {
          this.$router.push('/');
        } else {
          this.errorMessage = response.data.msg || '登录失败';
        }
      } catch (error) {
        this.errorMessage = this.getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },

    getErrorMessage(error) {
      if (error.response) {
        switch (error.response.status) {
          case 401:
            return '用户名或密码错误';
          case 500:
            return '服务器错误，请稍后再试';
          default:
            return '登录失败，请重试';
        }
      }
      return '网络连接异常，请检查网络';
    }
  }
};
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 50px auto;
  padding: 30px;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

button {
  width: 100%;
  padding: 12px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.error-msg {
  margin-top: 15px;
  color: #f56c6c;
  text-align: center;
}
</style>

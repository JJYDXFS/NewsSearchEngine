# NewsSearchEngine
create index for news document and provide a search interface

## 建立倒排索引

### 预处理

### 基于内存

### 基于磁盘

## 布尔检索

定义 AND OR ANDNOT 三种运算

运算符优先级表格

| op1/op2 | (    | )    | AND  | OR   | ANDNOT |
| ------- | ---- | ---- | ---- | ---- | ------ |
| (       | <    | =    | <    | <    | <      |
| )       | !    | >    | >    | >    | >      |
| AND     | <    | >    | >    | >    | >      |
| OR      | <    | >    | <    | >    | <      |
| ANDNOT  | <    | >    | >    | >    | >      |

中缀表达式转后缀，基于中间结果运算，栈空得结果

> input1: '孩子' 'AND' '教育'
>
> input2: '学生' ANDNOT '孩子'

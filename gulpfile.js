var gulp = require('gulp');
var sass = require('gulp-sass');
var watch = require('gulp-watch');
var minifycss = require('gulp-minify-css');
var rename = require('gulp-rename');
var gutil = require('gulp-util');

var dirs = {
  src: {
    style: 'hourglass_site/static_source/style/',
  },
  dest: {
    style: 'hourglass_site/static/hourglass_site/style/built/',
  }
};

var paths = {
  sass: '**/*.scss',
};

// default task
// running `gulp` will default to watching and dist'ing files
gulp.task('default', ['watch']);

// production build task
// will need to run before collectstatic
// `npm run gulp -- build` or `gulp run build` if gulp-cli is installed globally
gulp.task('build', ['sass']);

// compile SASS sources
gulp.task('sass', function () {
    return gulp.src(dirs.src.style + paths.sass)
        .pipe(sass())
        .pipe(gulp.dest(dirs.dest.style))
        .pipe(rename({suffix: '.min'}))
        .pipe(minifycss())
        .pipe(gulp.dest(dirs.dest.style));
});

// watch files for changes
gulp.task('watch', ['sass'], function () {
    gulp.watch(dirs.src.style + paths.sass, ['sass']);
});

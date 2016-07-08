var gulp = require('gulp');
var sass = require('gulp-sass');
var watch = require('gulp-watch');
var minifycss = require('gulp-minify-css');
var rename = require('gulp-rename');
var gzip = require('gulp-gzip');
var gutil = require('gulp-util');

var dirs = {
  src: {
    style: 'hourglass_site/static_source/style/',
  },
  dest: {
    style: 'hourglass_site/static/hourglass_site/style/',
  }
};

var paths = {
  sass: '**/*.scss',
};

// running `gulp` will default to watching and dist'ing files
gulp.task('default', ['watch']);

// production build
// will need to run before collectstatic
// `npm run gulp -- build`
gulp.task('build', ['sass']);


// compile SASS
gulp.task('sass', function () {
    return gulp.src(dirs.src.style + paths.sass)
        .pipe(sass())
        .pipe(gulp.dest(dirs.dest.style))
        .pipe(rename({suffix: '.min'}))
        .pipe(minifycss())
        .pipe(gulp.dest(dirs.dest.style))
        .pipe(gzip({
            threshold: '1kb',
            gzipOptions: {
                level: 9
            }
        }))
        .pipe(gulp.dest(dirs.dest.style));
});

// watch files for changes
gulp.task('watch', ['sass'], function () {
    gulp.watch(dirs.src.style + paths.sass, ['sass']);
});
